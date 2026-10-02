from inspect import signature
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult

from cms.services.telegram.base import _send_telegram_message_task


class Command(BaseCommand):
    help = "Requeue one failed Telegram task once; a timeout may have delivered the original message."

    def add_arguments(self, parser):
        parser.add_argument("task_id", type=UUID)

    def handle(self, task_id, **options):
        with transaction.atomic():
            try:
                result = DBTaskResult.objects.select_for_update().get(pk=task_id)
            except DBTaskResult.DoesNotExist:
                raise CommandError("Task not found") from None
            if result.status != TaskResultStatus.FAILED:
                raise CommandError("Only failed tasks can be retried")
            if result.task_path != "cms.services.telegram.base._send_telegram_message_task":
                raise CommandError("This command only retries Telegram delivery tasks")
            try:
                params = (
                    signature(_send_telegram_message_task.func)
                    .bind(*result.args_kwargs.get("args", []), **result.args_kwargs.get("kwargs", {}))
                    .arguments
                )
            except TypeError:
                raise CommandError("Unexpected task parameters; inspect the task manually") from None
            params.pop("token", None)
            # Reuse one row rather than create unlimited retry chains; retaining
            # the row ID makes the manual retry observable and avoids doubles.
            result.args_kwargs = {"args": [], "kwargs": params}
            result.status = TaskResultStatus.READY
            result.started_at = None
            result.finished_at = None
            result.exception_class_path = ""
            result.traceback = ""
            result.save(
                update_fields=[
                    "args_kwargs",
                    "status",
                    "started_at",
                    "finished_at",
                    "exception_class_path",
                    "traceback",
                ]
            )
        self.stdout.write(f"Queued Telegram task {task_id}. A previous timed-out delivery may be duplicated.")
