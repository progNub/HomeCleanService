"""Track host-side certificate operations in the Django task backend."""

import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django_tasks.base import TaskResultStatus
from django_tasks_db.models import DBTaskResult

from cms.tasks import renew_certificate_task

TASK_PATH = "cms.tasks.renew_certificate_task"
WORKER_ID = "systemd:certificate-renewal"
MAX_OUTPUT_LENGTH = 16_000


class Command(BaseCommand):
    help = "Create, claim, or finish a host-managed certificate renewal task"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)

        enqueue = subparsers.add_parser("enqueue")
        enqueue.add_argument("--mode", choices=("renew", "dry-run"), default="renew")

        claim = subparsers.add_parser("claim")
        claim.add_argument("task_id")

        finish = subparsers.add_parser("finish")
        finish.add_argument("task_id")
        finish.add_argument("--status", choices=("successful", "failed"), required=True)

    def handle(self, *args, **options):
        action = options["action"]
        if action == "enqueue":
            result = renew_certificate_task.enqueue(mode=options["mode"])
            self.stdout.write(str(result.id))
            return

        if action == "claim":
            with transaction.atomic():
                task_result = self._get_locked_task(options["task_id"])
                if task_result.status != TaskResultStatus.READY:
                    raise CommandError("Certificate task is not ready")
                task_result.claim(WORKER_ID)
            return

        output = self._safe_output(sys.stdin.read())
        with transaction.atomic():
            task_result = self._get_locked_task(options["task_id"])
            if task_result.status != TaskResultStatus.RUNNING:
                raise CommandError("Certificate task is not running")

            if options["status"] == "successful":
                task_result.set_successful(
                    {
                        "operation": self._operation(task_result),
                        "output": output or "Certificate operation completed without output.",
                    }
                )
            else:
                task_result.status = TaskResultStatus.FAILED
                task_result.finished_at = timezone.now()
                task_result.return_value = None
                task_result.exception_class_path = "cms.tasks.CertificateRenewalError"
                task_result.traceback = output or "Certificate operation failed without output."
                task_result.save(
                    update_fields=(
                        "status",
                        "finished_at",
                        "return_value",
                        "exception_class_path",
                        "traceback",
                    )
                )

    @staticmethod
    def _safe_output(output):
        output = output.strip()
        if len(output) <= MAX_OUTPUT_LENGTH:
            return output
        return f"{output[:MAX_OUTPUT_LENGTH]}\n[output truncated]"

    @staticmethod
    def _operation(task_result):
        return task_result.args_kwargs.get("kwargs", {}).get("mode", "renew")

    @staticmethod
    def _get_locked_task(task_id):
        try:
            return DBTaskResult.objects.select_for_update().get(pk=task_id, task_path=TASK_PATH)
        except (DBTaskResult.DoesNotExist, ValueError) as exc:
            raise CommandError("Certificate task was not found") from exc
