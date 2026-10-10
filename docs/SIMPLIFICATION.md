# Simplification review: July 24 to the latest local changes

Baseline: `37d6784` (July 24, 2026), compared with `778f4f6` and the current
uncommitted simplifications. This is a small Django/Wagtail site, not a platform
that needs additional deployment environments, brokers or orchestration services.

## What became unnecessarily difficult

| Before July baseline | After hardening | Simplified behavior |
| --- | --- | --- |
| `make dev-start`: five containers | Only DB/Redis; three profiles to remember | All five again: DB, Redis, worker, Umami, Dozzle |
| `make run`: Django on host | Same, but obscured by other commands | Unchanged; `make dev-run` combines infrastructure and Django startup |
| Background tasks worked locally | Ignored restore settings disabled the entire queue | Real database queue; worker shares the site's restored database/settings |
| Telegram could be tested locally | Restore-specific overrides disabled it | Uses the configured local `.env` again, by explicit request |
| Familiar logs page | Dozzle was optional and required a separate command | Starts with development; existing authentication retained |
| Shorter manual operations | Image digest needed even for backup/cert maintenance | Reuse last successful image automatically; explicit override still supported |
| One large command list | More advanced deployment commands mixed into daily help | Short `make help`; full list remains in `make help-all` |

The dev network and volume ownership labels remain compatible with existing
containers/data. The separate `docker-compose.build.yml` was already removed;
the common/dev/prod split is retained as requested. Certbot remains a separate
one-off operation, not another environment to launch for daily development.

## What is worth keeping

- Responsive frontend/assets, local dependencies and build-time static files:
  no Node/Sass or asset compilation on live requests.
- One Django application, existing PostgreSQL task queue, no Celery/new broker.
- Explicit production secrets, excluded local settings/backups, non-root runtime.
- Form validation, request limits, safe redirects and reliable recording of leads.
- Tested release image, backup before migration, one migration step, Nginx config
  validation and post-release health checks. These prevent concrete release failures.
- Local restore, certificate renewal and optional encrypted offsite backups. They
  are maintenance operations, not prerequisites for editing a page or running dev.
- The read-only Wagtail task screen; it reuses the existing model without migrations.

The production path remains intentionally manual: checks, merge, explicit GitHub
Actions release. Removing backup/health checks or returning migrations to every
web/worker startup would reduce visible code but weaken correctness, not simplify
the workflow. A failed migration still has no automatic database rollback.

## Boundaries

No production deployment, push or new commit is part of this simplification.
The ignored local restore settings were adjusted without changing the selected
database or media directory. Email remains disabled for that restored copy;
Telegram now sends to configured chats when the user tests notifications.
Tests use isolated settings and never send real Telegram messages.

No new persistent local-production environment or JSON logging stack was added.
Certificate dry-run succeeded earlier, but its server timer is not installed yet.
