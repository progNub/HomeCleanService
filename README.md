# HomeService

Django/Wagtail site with server-rendered templates, StreamField content and Bootstrap.
PostgreSQL stores content and background tasks; Redis provides production caching.
Node is needed to build frontend assets, not to run the production application.

## Development

Requirements: Python 3.12, uv, Node.js 22, Docker with Compose v2, and Make.
The usual setup runs **five containers** (PostgreSQL, Redis, task worker, Umami,
Dozzle) and Django on the host. No profiles need to be remembered for development.

For an already configured checkout, run:

```bash
make dev-run
```

Or use `make dev-start` and then `make run` in your IDE/terminal as before.
`make dev-up` starts those same five containers and follows their logs; it does
not start Django. `make dev-down` stops the containers without deleting data.
`make help` shows daily commands; `make help-all` includes advanced maintenance.

| What | Where |
| --- | --- |
| Site / Wagtail | http://localhost:8000/ / http://localhost:8000/admin/ |
| Container logs (Dozzle, login required) | http://localhost:8081/ |
| Analytics (Umami) | http://localhost:3000/ |
| Django logs | Terminal running `make run` |

The host site and container worker use the same development settings, including
an ignored `settings/local.py` if present. Only the database network address
differs. Tasks are stored in PostgreSQL and are visible under **Фоновые задачи**
in Wagtail. Telegram sends to the bot/chat configured in `.env`; use test
credentials when you do not want real notifications. Never print/share `.env`.

### First setup only

Do not overwrite an existing `.env` or reinitialize an already restored database.
For a new checkout, configure `.env`, then set up Dozzle credentials once as
described in [log access](docs/LOGS.md). There is no automatic default password.

```bash
cp .env.example .env
uv sync --frozen
npm ci
npm run build
docker compose -p homeservice-dev -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up -d --wait db redis
make migrate
make superuser
make dev-run
```

Edit `.env` before starting. PostgreSQL listens on `127.0.0.1:5433`, Redis on
`127.0.0.1:6380`, and Django on [localhost:8000](http://localhost:8000).
The worker starts automatically; no second host worker is needed. Its dedicated
development build uses the same locked Python dependencies without building the
frontend. `make dev-start` reuses Docker build cache and waits for service readiness.

### Compose layout

- `deploy/docker-compose.yml`: shared PostgreSQL, Redis, Umami and Dozzle definitions,
  pinned image versions, health checks and bounded container logs. Not a standalone environment.
- `deploy/docker-compose.dev.yml`: development overrides (loopback ports and the
  local worker build). All five services start normally; Django runs with `make run`.
- `deploy/docker-compose.prod.yml`: production overrides and application services,
  Nginx/TLS, mandatory secrets and an already-built `APP_IMAGE`.

Makefile commands combine the base with exactly one environment file, in that order.
Direct Compose commands must do the same using two `-f` options. Development and
production retain their existing project, network and physical volume names;
development volume aliases explicitly retain the old `_dev` suffixes.

`make prod-build` builds `homeservice:local` directly from the Dockerfile with the
current revision label; it does not start containers or deploy. The former
`docker-compose.build.yml` only added this build instruction and is no longer needed.
CI still builds and tests the release image, and production deploys its immutable digest.
`deploy/certbot/docker-compose.yml` remains a separate one-off operations configuration
using the existing production certificate volumes; it is not a fourth runtime environment.

For a new empty database, `.venv/bin/python manage.py init_site` explicitly seeds
sample pages/settings. Review its content and optional `SUPERUSER_*` variables
first. It never runs automatically at application startup.

Run `npm run build:watch` while editing SCSS. `npm run build` generates ignored
`cms/static/cms/dist/` with compiled CSS, local Bootstrap JS and icon fonts.
JavaScript in `cms/static/cms/js/` is served directly. Rebuild after updating npm
dependencies; commit package files and the lock, not generated assets.

## Checks

```bash
make check
make test
npm run build
```

Django tests use isolated SQLite, local cache and dummy task delivery by default;
they do not use development `.env` or send Telegram messages. CI also checks
the PostgreSQL path and production image, including an isolated Nginx HTTPS stack.
To run that container check locally without real .env, host ports or external providers:

```bash
HOMESERVICE_TEST_IMAGE=homeservice:local bash tests/container-smoke.sh
```

Build the image first with `make prod-build`. Temporary containers, volumes and
network are removed automatically. Tests do not replace a production smoke
check or a backup restore drill.

## Production

Follow [the deployment guide](docs/DEPLOYMENT.md) for installation and migration
of an existing server. Releases use a tested image digest and its exact Git
revision. `make prod-start` performs a short maintenance-window deployment with
backup, one-time migrations/assets release, startup and HTTPS smoke checks.
CI supplies the tested `APP_IMAGE`; it does not build from the server checkout.
After a successful release, Makefile and maintenance scripts can reuse the image
recorded in `deploy/.release/current-image`. You do not need to copy its digest for
ordinary log viewing, backups or certificate renewal. An explicit `APP_IMAGE` wins.

For an intentional local Docker build:

```bash
make prod-build
ALLOW_LOCAL_IMAGE=1 APP_IMAGE=homeservice:local make prod-start
```

This still needs production configuration, writable data directories and working
HTTPS. Use `make prod-init` instead of `prod-start` only for an empty first
installation. A manual workflow run on master with deploy=true publishes to GHCR
and deploys after checks pass; normal pushes/PRs only run checks.

## Structure and operations

| Path | Purpose |
| --- | --- |
| `cms/models/pages/`, `cms/blocks/` | Wagtail pages and reusable content blocks |
| `cms/templates/`, `cms/static/cms/` | HTML templates, SCSS and small JS modules |
| `cms/services/`, `cms/logging/` | Integrations, notifications and queued logging |
| `settings/` | Development, production, build and isolated test settings |
| `deploy/`, `.github/workflows/` | Compose, operations scripts and CI |
| `cms/tests/`, `tests/` | Application and operations checks |

Useful commands: `make help`, `make prod-logs-web`, `make prod-smoke`,
`make prod-db-backup`, `make cert-dry-run`.

- [Deployment and rollback](docs/DEPLOYMENT.md)
- [Backups and restore drills](deploy/docs/backups.md)
- [Certificate issuance and renewal](deploy/docs/ssl.md)
- [Private Dozzle access](docs/LOGS.md)
- [Umami](deploy/docs/umami.md), [localization](locale/README.md)
