"""Read-only monitoring of the existing database-backed task queue."""

import json

from django.contrib.auth import get_user_model
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tasks_db.models import DBTaskResult
from wagtail import hooks
from wagtail.admin.views.generic import InspectView
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.permission_policies.base import ModelPermissionPolicy


class TaskResultPermissionPolicy(ModelPermissionPolicy):
    def user_has_permission(self, user, action):
        return action == "view" and super().user_has_permission(user, action)

    def users_with_any_permission(self, actions):
        if "view" not in actions:
            return get_user_model().objects.none()
        return super().users_with_any_permission(["view"])


class TaskResultInspectView(InspectView):
    page_title = _("Результат фоновой задачи")

    def get_page_subtitle(self):
        # Do not import the task callable: old deployments may have removed it.
        return self.object.task_path

    def get_traceback_display_value(self):
        return format_html('<pre class="w-wrap-anywhere">{}</pre>', self.object.traceback or "—")

    def get_return_value_display_value(self):
        value = json.dumps(self.object.return_value, ensure_ascii=False, indent=2)
        return format_html('<pre class="w-wrap-anywhere">{}</pre>', value)


class TaskResultViewSet(ModelViewSet):
    model = DBTaskResult
    icon = "tasks"
    menu_label = _("Фоновые задачи")
    add_to_admin_menu = True
    add_to_reference_index = False
    permission_policy = TaskResultPermissionPolicy(DBTaskResult)
    copy_view_enabled = False
    inspect_view_enabled = True
    inspect_view_class = TaskResultInspectView
    list_display = ("task_path", "status", "queue_name", "enqueued_at", "started_at", "finished_at")
    list_filter = ("status", "queue_name")
    search_fields = ("task_path",)
    search_backend_name = None
    ordering = ("-enqueued_at", "-id")
    list_per_page = 25
    # Never expose arguments: legacy jobs may contain tokens or personal data.
    inspect_view_fields = (
        "id",
        "task_path",
        "status",
        "queue_name",
        "backend_name",
        "priority",
        "enqueued_at",
        "run_after",
        "started_at",
        "finished_at",
        "return_value",
        "exception_class_path",
        "traceback",
    )

    def get_urlpatterns(self):
        # Do not register mutation endpoints, even for superusers.
        return [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
            path("inspect/<uuid:pk>/", self.inspect_view, name="inspect"),
        ]

    def get_permissions_to_register(self):
        return super().get_permissions_to_register().filter(codename="view_dbtaskresult")


task_results_viewset = TaskResultViewSet("background-tasks")


@hooks.register("register_admin_viewset")
def register_task_results_viewset():
    return task_results_viewset
