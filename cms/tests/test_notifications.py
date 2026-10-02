import traceback
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult

from cms.services.telegram.base import RawTelegramService, TelegramDeliveryError, _send_telegram_message_task
from cms.services.telegram.notifications import LeadNotificationService


@override_settings(TELEGRAM_BOT_TOKEN="test-secret", TELEGRAM_NOTIFICATIONS_CHAT_ID="123")
class NotificationTests(TestCase):
    def test_review_and_lead_values_are_escaped(self):
        service = LeadNotificationService()
        text = service._format_review(SimpleNamespace(author="<b>A</b>", text="<i>B & C</i>", rating=5))
        self.assertIn("&lt;b&gt;A&lt;/b&gt;", text)
        self.assertIn("&lt;i&gt;B &amp; C&lt;/i&gt;", text)
        submission = SimpleNamespace(page=None, form_data={"<key>": "<value>"})
        self.assertIn("&lt;key&gt;", service._format_formsubmission(submission))
        self.assertIn("&lt;value&gt;", service._format_formsubmission(submission))

    @patch("cms.services.telegram.base._send_telegram_message_task")
    def test_enqueue_waits_for_commit_and_never_persists_token(self, task):
        with self.captureOnCommitCallbacks(execute=True):
            RawTelegramService().send_raw("hello")
            task.enqueue.assert_not_called()
        task.enqueue.assert_called_once()
        self.assertNotIn("token", task.enqueue.call_args.kwargs)

    @patch("cms.services.telegram.base._send_telegram_message_task")
    def test_rolled_back_submission_does_not_enqueue(self, task):
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(ValueError), transaction.atomic():
                RawTelegramService().send_raw("hello")
                raise ValueError("rollback")
        task.enqueue.assert_not_called()

    @patch("cms.services.telegram.base.requests.post")
    def test_delivery_failure_is_visible_without_provider_secrets(self, post):
        post.side_effect = requests.Timeout("https://api.telegram.org/bottest-secret user text")
        try:
            _send_telegram_message_task.call(chat_id="123", text="hello")
        except TelegramDeliveryError:
            rendered = traceback.format_exc()
        else:
            self.fail("Transport errors must mark the task failed")
        self.assertNotIn("test-secret", rendered)
        self.assertNotIn("user text", rendered)

    @patch("cms.services.telegram.base.requests.post")
    def test_http_and_api_rejections_raise_sanitized_failure(self, post):
        post.return_value = Mock(ok=False, status_code=429)
        with self.assertRaisesRegex(TelegramDeliveryError, "HTTP 429"):
            _send_telegram_message_task.call(chat_id="123", text="hello")
        post.return_value = Mock(ok=True, json=Mock(return_value={"ok": False, "description": "private"}))
        with self.assertRaisesRegex(TelegramDeliveryError, "rejected"):
            _send_telegram_message_task.call(chat_id="123", text="hello")

    @patch("cms.services.telegram.base.requests.post")
    def test_old_queued_kwargs_remain_compatible_using_current_token(self, post):
        post.return_value = Mock(ok=True, json=Mock(return_value={"ok": True}))
        _send_telegram_message_task.call(
            token="stale-secret",
            chat_id="123",
            text="hello",
            parse_mode="HTML",
            timeout=10,
            api_endpoint="https://api.telegram.org",
        )
        self.assertIn("bottest-secret/", post.call_args.args[0])
        self.assertNotIn("stale-secret", post.call_args.args[0])

    def test_retry_only_requeues_failed_telegram_task_and_strips_token(self):
        result = DBTaskResult.objects.create(
            status=TaskResultStatus.FAILED,
            task_path="cms.services.telegram.base._send_telegram_message_task",
            backend_name="default",
            run_after=timezone.now(),
            args_kwargs={"args": [], "kwargs": {"token": "old-secret", "chat_id": "123", "text": "hello"}},
        )
        call_command("retry_telegram", str(result.id), verbosity=0)
        result.refresh_from_db()
        self.assertEqual(result.status, TaskResultStatus.READY)
        self.assertNotIn("token", result.args_kwargs["kwargs"])
        with self.assertRaises(CommandError):
            call_command("retry_telegram", str(result.id))
        result.status = TaskResultStatus.FAILED
        result.task_path = "unrelated.task"
        result.save()
        with self.assertRaises(CommandError):
            call_command("retry_telegram", str(result.id))
