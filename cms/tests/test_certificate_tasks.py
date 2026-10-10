import io
from unittest.mock import patch

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult

from cms.management.commands.certificate_task import MAX_OUTPUT_LENGTH, TASK_PATH, WORKER_ID


@override_settings(
    TASKS={
        "default": {
            "BACKEND": "django_tasks_db.DatabaseBackend",
            "QUEUES": ["default", "notifications", "maintenance"],
        }
    }
)
class CertificateTaskCommandTests(TestCase):
    def enqueue(self, mode="renew"):
        stdout = io.StringIO()
        call_command("certificate_task", "enqueue", "--mode", mode, stdout=stdout)
        return DBTaskResult.objects.get(pk=stdout.getvalue().strip())

    def test_maintenance_queue_is_declared_but_not_used_by_regular_worker(self):
        self.assertIn("maintenance", settings.TASKS["default"]["QUEUES"])

    def test_enqueue_and_claim_create_a_visible_host_managed_task(self):
        task_result = self.enqueue("dry-run")

        self.assertEqual(task_result.task_path, TASK_PATH)
        self.assertEqual(task_result.queue_name, "maintenance")
        self.assertEqual(task_result.status, TaskResultStatus.READY)
        self.assertEqual(task_result.args_kwargs["kwargs"], {"mode": "dry-run"})

        call_command("certificate_task", "claim", str(task_result.pk))
        task_result.refresh_from_db()
        self.assertEqual(task_result.status, TaskResultStatus.RUNNING)
        self.assertEqual(task_result.worker_ids, [WORKER_ID])
        self.assertIsNotNone(task_result.started_at)

    def test_successful_result_keeps_safe_output(self):
        task_result = self.enqueue()
        call_command("certificate_task", "claim", str(task_result.pk))

        with patch("sys.stdin", io.StringIO("Certificate not yet due for renewal.\n")):
            call_command("certificate_task", "finish", str(task_result.pk), "--status", "successful")

        task_result.refresh_from_db()
        self.assertEqual(task_result.status, TaskResultStatus.SUCCESSFUL)
        self.assertEqual(task_result.return_value["operation"], "renew")
        self.assertEqual(task_result.return_value["output"], "Certificate not yet due for renewal.")
        self.assertIsNotNone(task_result.finished_at)

    def test_failed_result_is_visible_and_long_output_is_bounded(self):
        task_result = self.enqueue()
        call_command("certificate_task", "claim", str(task_result.pk))

        with patch("sys.stdin", io.StringIO("x" * (MAX_OUTPUT_LENGTH + 20))):
            call_command("certificate_task", "finish", str(task_result.pk), "--status", "failed")

        task_result.refresh_from_db()
        self.assertEqual(task_result.status, TaskResultStatus.FAILED)
        self.assertEqual(task_result.exception_class_path, "cms.tasks.CertificateRenewalError")
        self.assertTrue(task_result.traceback.endswith("[output truncated]"))
        self.assertLessEqual(len(task_result.traceback), MAX_OUTPUT_LENGTH + 20)

    def test_cannot_finish_an_unclaimed_task(self):
        task_result = self.enqueue()

        with patch("sys.stdin", io.StringIO("output")), self.assertRaises(CommandError):
            call_command("certificate_task", "finish", str(task_result.pk), "--status", "successful")
