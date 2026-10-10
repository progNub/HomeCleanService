"""Task declarations for operations executed by trusted external runners."""

from django.tasks import task


class ExternalMaintenanceRunnerRequired(RuntimeError):
    """Raised when a host-only task is consumed by a regular Django worker."""


@task(queue_name="maintenance")
def renew_certificate_task(mode="renew"):
    """Represent certificate renewal in the task backend.

    The systemd runner claims and completes this task because only the host is
    allowed to run Docker and reload Nginx. The application worker must never
    receive those privileges.
    """
    raise ExternalMaintenanceRunnerRequired(f"Certificate operation {mode!r} requires the host maintenance runner")
