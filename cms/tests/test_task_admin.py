from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult

from cms.wagtail_hooks.tasks import task_results_viewset


class TaskAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser("task-admin", "admin@example.test", "test-password")
        cls.editor = get_user_model().objects.create_user("task-editor", password="test-password")
        cls.editor.user_permissions.add(Permission.objects.get(codename="access_admin"))
        cls.view_permission = Permission.objects.get(
            content_type__app_label=DBTaskResult._meta.app_label, codename="view_dbtaskresult"
        )
        cls.task = DBTaskResult.objects.create(
            task_path="removed.module.notification",
            status=TaskResultStatus.FAILED,
            queue_name="notifications",
            backend_name="default",
            run_after=timezone.now(),
            args_kwargs={"args": [], "kwargs": {"token": "legacy-secret", "text": "private-arguments"}},
            return_value={"message": "<script>unsafe-result</script>"},
            exception_class_path="example.DeliveryError",
            traceback="<script>unsafe-traceback</script>\nDeliveryError: delivery failed",
        )

    def setUp(self):
        self.index_url = reverse("background-tasks:index")
        self.inspect_url = reverse("background-tasks:inspect", args=[self.task.pk])

    def test_anonymous_user_must_log_in(self):
        for url in (self.index_url, self.inspect_url, reverse("background-tasks:index_results")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("wagtailadmin_login"), response.url)

    def test_editor_without_view_permission_cannot_see_tasks_or_menu(self):
        self.client.force_login(self.editor)
        for url in (self.index_url, self.inspect_url, reverse("background-tasks:index_results")):
            self.assertEqual(self.client.get(url).status_code, 302)
        request = RequestFactory().get(self.index_url)
        request.user = self.editor
        self.assertFalse(task_results_viewset.get_menu_item().is_shown(request))

    def test_view_permission_allows_list_details_and_menu(self):
        self.editor.user_permissions.add(self.view_permission)
        self.client.force_login(self.editor)
        self.assertContains(self.client.get(self.index_url), self.task.task_path)
        self.assertContains(self.client.get(self.inspect_url), "DeliveryError: delivery failed")
        request = RequestFactory().get(self.index_url)
        request.user = get_user_model().objects.get(pk=self.editor.pk)
        self.assertTrue(task_results_viewset.get_menu_item().is_shown(request))

    def test_details_escape_result_and_error_and_hide_arguments(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.inspect_url)
        self.assertContains(response, "&lt;script&gt;unsafe-result&lt;/script&gt;")
        self.assertContains(response, "&lt;script&gt;unsafe-traceback&lt;/script&gt;")
        self.assertNotContains(response, "<script>unsafe-")
        self.assertNotContains(response, "legacy-secret")
        self.assertNotContains(response, "private-arguments")
        self.assertContains(response, self.task.task_path)

    def test_list_filters_search_ordering_and_pagination(self):
        self.client.force_login(self.superuser)
        newer = DBTaskResult.objects.create(
            task_path="other.success_task",
            status=TaskResultStatus.SUCCESSFUL,
            backend_name="default",
            run_after=timezone.now(),
            args_kwargs={"args": [], "kwargs": {}},
        )
        response = self.client.get(self.index_url)
        self.assertEqual(list(response.context["object_list"]), [newer, self.task])
        for query in ({"status": "FAILED"}, {"queue_name": "notifications"}, {"q": "notification"}):
            with self.subTest(query=query):
                response = self.client.get(self.index_url, query)
                self.assertEqual(list(response.context["object_list"]), [self.task])
        self.assertEqual(response.context["paginator"].per_page, 25)

    def test_even_superusers_cannot_mutate_tasks(self):
        self.client.force_login(self.superuser)
        for action in ("add", "change", "delete"):
            self.assertFalse(task_results_viewset.permission_policy.user_has_permission(self.superuser, action))
        for name in ("add", "edit", "delete", "copy"):
            with self.subTest(name=name), self.assertRaises(NoReverseMatch):
                reverse(f"background-tasks:{name}", args=[] if name == "add" else [self.task.pk])
        for url in (self.index_url, self.inspect_url, reverse("background-tasks:index_results")):
            self.assertEqual(self.client.post(url, {"status": "READY"}).status_code, 405)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskResultStatus.FAILED)
        self.assertEqual(DBTaskResult.objects.count(), 1)

    def test_only_view_permission_is_registered_in_wagtail(self):
        self.assertEqual(list(task_results_viewset.get_permissions_to_register()), [self.view_permission])
