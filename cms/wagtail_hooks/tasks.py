"""Read-only, generic monitoring for the database-backed task queue."""

import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult
from wagtail import hooks
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.views.generic import InspectView
from wagtail.admin.views.generic.models import IndexView
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.permission_policies.base import ModelPermissionPolicy

STATUS_LABELS = {
    TaskResultStatus.READY: _("Queued"),
    TaskResultStatus.RUNNING: _("Running"),
    TaskResultStatus.FAILED: _("Failed"),
    TaskResultStatus.SUCCESSFUL: _("Successful"),
}
SENSITIVE_KEY_PATTERN = re.compile(
    r"(^|[_-])(authorization|cookie|credential|password|private[_-]?key|secret|token|api[_-]?key)([_-]|$)",
    re.IGNORECASE,
)
TELEGRAM_TOKEN_PATTERN = re.compile(r"(api\.telegram\.org/bot)[^/\s]+", re.IGNORECASE)
BEARER_TOKEN_PATTERN = re.compile(r"(bearer\s+)[^\s]+", re.IGNORECASE)
REDACTED_VALUE = _("[redacted]")


def _task_title(task_result):
    """Return a readable title without maintaining a per-task name registry."""
    short_name = task_result.task_path.rsplit(".", 1)[-1]
    title = short_name.lstrip("_").removesuffix("_task").replace("_", " ").strip()
    return title.capitalize() or task_result.task_path


def _status_label(task_result):
    return STATUS_LABELS.get(task_result.status, str(task_result.status).capitalize())


def _status_class(task_result):
    status = str(task_result.status).lower()
    return status if status in {"ready", "running", "failed", "successful"} else "unknown"


def _status_badge(task_result):
    return format_html(
        '<span class="task-status task-status--{}">{}</span>',
        _status_class(task_result),
        _status_label(task_result),
    )


def _queue_name(task_result):
    return task_result.queue_name or "default"


def _duration(task_result):
    if not task_result.started_at:
        return "—"
    finished_at = task_result.finished_at
    if not finished_at and task_result.status == TaskResultStatus.RUNNING:
        finished_at = timezone.now()
    if not finished_at:
        return "—"
    seconds = max((finished_at - task_result.started_at).total_seconds(), 0)
    if seconds < 10:
        return f"{seconds:.1f} s"
    if seconds < 60:
        return f"{seconds:.0f} s"
    minutes, remaining = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes} min {remaining} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min {remaining} s"


def _redact_text(value):
    text = str(value)
    configured_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if configured_token:
        text = text.replace(str(configured_token), str(REDACTED_VALUE))
    text = TELEGRAM_TOKEN_PATTERN.sub(rf"\1{REDACTED_VALUE}", text)
    return BEARER_TOKEN_PATTERN.sub(rf"\1{REDACTED_VALUE}", text)


def _format_scalar(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return _redact_text(value)


def _flatten_data(value, path=""):
    """Flatten arbitrary JSON into generic key/value rows for the inspector."""
    if isinstance(value, dict):
        if not value:
            return [{"key": path or str(_("Value")), "value": "{}"}]
        rows = []
        for key, nested_value in value.items():
            key = str(key)
            nested_path = f"{path}.{key}" if path else key
            if SENSITIVE_KEY_PATTERN.search(key):
                rows.append({"key": nested_path, "value": str(REDACTED_VALUE), "redacted": True})
            else:
                rows.extend(_flatten_data(nested_value, nested_path))
        return rows

    if isinstance(value, (list, tuple)):
        if not value:
            return [{"key": path or str(_("Value")), "value": "[]"}]
        rows = []
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"[{index}]"
            rows.extend(_flatten_data(nested_value, nested_path))
        return rows

    return [{"key": path or str(_("Value")), "value": _format_scalar(value)}]


def _workers(task_result):
    worker_ids = task_result.worker_ids
    if not worker_ids:
        return "—"
    if isinstance(worker_ids, (list, tuple)):
        return ", ".join(str(worker_id) for worker_id in worker_ids)
    return str(worker_ids)


class TaskResultPermissionPolicy(ModelPermissionPolicy):
    def user_has_permission(self, user, action):
        return action == "view" and super().user_has_permission(user, action)

    def users_with_any_permission(self, actions):
        if "view" not in actions:
            return get_user_model().objects.none()
        return super().users_with_any_permission(["view"])


class TaskResultIndexView(IndexView):
    page_title = _("Background tasks")


class TaskResultInspectView(InspectView):
    template_name = "cms/background_tasks_inspect.html"
    page_title = _("Background task")

    def get_page_subtitle(self):
        return _task_title(self.object)

    def get_fields_context(self):
        # The custom template uses universal sections instead of model-specific fields.
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "status_label": _status_label(self.object),
                "status_class": _status_class(self.object),
                "summary_rows": (
                    {"label": _("Task ID"), "value": self.object.pk, "code": True},
                    {"label": _("Task"), "value": _task_title(self.object)},
                    {"label": _("Task path"), "value": self.object.task_path, "code": True},
                    {"label": _("Queue"), "value": _queue_name(self.object), "code": True},
                    {"label": _("Backend"), "value": self.object.backend_name or "—", "code": True},
                    {"label": _("Priority"), "value": self.object.priority},
                    {"label": _("Enqueued"), "value": self.object.enqueued_at, "datetime": True},
                    {"label": _("Scheduled for"), "value": self.object.run_after, "datetime": True},
                    {"label": _("Started"), "value": self.object.started_at, "datetime": True},
                    {"label": _("Finished"), "value": self.object.finished_at, "datetime": True},
                    {"label": _("Duration"), "value": _duration(self.object)},
                    {"label": _("Workers"), "value": _workers(self.object), "code": True},
                ),
                "input_rows": _flatten_data(self.object.args_kwargs),
                "result_rows": _flatten_data(self.object.return_value),
                "error_rows": (
                    {
                        "key": str(_("Exception")),
                        "value": _redact_text(self.object.exception_class_path or "—"),
                    },
                    {
                        "key": str(_("Traceback")),
                        "value": _redact_text(self.object.traceback or "—"),
                    },
                ),
                "has_error": bool(self.object.exception_class_path or self.object.traceback),
            }
        )
        return context


class TaskResultViewSet(ModelViewSet):
    model = DBTaskResult
    icon = "tasks"
    menu_label = _("Background tasks")
    add_to_admin_menu = True
    add_to_reference_index = False
    permission_policy = TaskResultPermissionPolicy(DBTaskResult)
    copy_view_enabled = False
    inspect_view_enabled = True
    index_view_class = TaskResultIndexView
    inspect_view_class = TaskResultInspectView
    list_display = (
        TitleColumn(
            "task_title",
            label=_("Task"),
            accessor=_task_title,
            get_url=lambda task_result: reverse("background-tasks:inspect", args=[task_result.pk]),
        ),
        Column("task_status", label=_("Status"), accessor=_status_badge),
        Column("queue", label=_("Queue"), accessor=_queue_name),
        Column("enqueued_at", label=_("Enqueued"), accessor="enqueued_at"),
        Column("started_at", label=_("Started"), accessor="started_at"),
        Column("finished_at", label=_("Finished"), accessor="finished_at"),
        Column("duration", label=_("Duration"), accessor=_duration),
    )
    list_filter = ("status", "queue_name")
    search_fields = ("task_path",)
    search_backend_name = None
    ordering = ("-enqueued_at", "-id")
    list_per_page = 25

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


@hooks.register("insert_global_admin_css")
def task_results_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static("cms/background-tasks.css"))
