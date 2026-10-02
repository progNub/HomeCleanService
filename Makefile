-include Makefile.config

# Confirmation helper
define confirm_action
	@echo -n "Are you sure you want to proceed with $(1)? [y/N] " && read ans && [ $${ans:-N} = y ]
endef

# Default values for local environment (can be overridden by environment variables)
PROJECT_DEV ?= homeservice-dev
PROJECT_PROD ?= homeservice-prod
DB_NAME ?= homeservice
DB_USER ?= homeservice_user

# Docker Compose commands
COMPOSE_DEV = docker compose -p $(PROJECT_DEV) -f deploy/docker-compose.dev.yml
HOMESERVICE_ENV_FILE ?= $(CURDIR)/.env
COMPOSE_PROD = docker compose --env-file $(HOMESERVICE_ENV_FILE) -p $(PROJECT_PROD) -f deploy/docker-compose.yml
COMPOSE_SSL = docker compose -p $(PROJECT_PROD) -f deploy/certbot/docker-compose.yml

# Python and Local Virtual Environment
VENV = .venv
PYTHON = $(VENV)/bin/python
MANAGE = $(PYTHON) manage.py

# Docker Execution command for Production
DOCKER_EXEC = $(COMPOSE_PROD) exec web

.PHONY: help dev-up dev-start dev-down dev-logs run prod-up prod-start prod-down prod-logs prod-logs-web prod-logs-dozzle dozzle-gen-pass prod-build prod-migrate prod-superuser prod-cache-clear prod-shell migrate superuser cache-clear dev-reset dev-db-refresh prod-reset prod-db-refresh cert prod-db-backup db-init-umami

# Default target: show help
help:
	@echo "Available commands:"
	@echo "  Development (Infrastructure in Docker + App locally):"
	@echo "    make dev-up            - Start DB/Redis and follow logs"
	@echo "    make dev-start         - Start DB/Redis in background"
	@echo "    make dev-down          - Stop development infrastructure"
	@echo "    make dev-logs          - Follow development infrastructure logs"
	@echo "    make run               - Run Django development server locally"
	@echo "    make assets            - Install locked npm dependencies and build static assets"
	@echo "    make check             - Check lockfile, Python style and Django configuration"
	@echo "    make test              - Run isolated application and operations tests"
	@echo ""
	@echo "  Production (Full stack in Docker):"
	@echo "    make prod-up           - Deploy APP_IMAGE with backup/checks, then follow logs"
	@echo "    make prod-start        - Deploy tested APP_IMAGE digest (maintenance window)"
	@echo "    make prod-init         - Bootstrap empty installation; content/TLS remain explicit"
	@echo "    make prod-smoke        - Verify external HTTPS readiness, homepage and assets"
	@echo "    make prod-rollback     - Restore compatible old image; ROLLBACK_DB_COMPATIBLE=1 required"
	@echo "    make prod-down         - Stop production stack"
	@echo "    make prod-logs         - Follow all production logs"
	@echo "    make prod-logs-web     - Follow only web container logs"
	@echo "    make prod-logs-dozzle   - Follow only Dozzle logs"
	@echo "    make prod-tools        - Start private loopback Dozzle with existing credentials"
	@echo "    make dozzle-gen-pass   - Write users.yml; set DOZZLE_USER and explicit DOZZLE_PASS"
	@echo "    make prod-build        - Build homeservice:local for explicit local testing"
	@echo "    make prod-migrate      - Manually run release migrations/assets job; stop writers first"
	@echo "    make prod-superuser    - Create superuser inside production container"
	@echo "    make prod-cache-clear  - Clear Wagtail cache inside production container"
	@echo "    make prod-shell        - Open Django shell inside production container"
	@echo "    make prod-reset        - NUCLEAR RESET: Stop, remove production volumes (DB + Stats) and start again"
	@echo "    make prod-db-refresh   - DJANGO ONLY RESET: Recreate Django DB, keeping Umami data"
	@echo ""
	@echo "  Clean up & Reset:"
	@echo "    make dev-reset         - NUCLEAR RESET: Stop, remove development volumes (DB + Stats) and start again"
	@echo "    make dev-db-refresh    - DJANGO ONLY RESET: Recreate Django DB locally, keeping Umami data"
	@echo ""
	@echo "  Backup & Maintenance:"
	@echo "    make prod-db-backup    - Back up DB/media with required encryption and off-host upload"
	@echo "    make prod-backup-local - Create local snapshot (not a disaster-recovery backup)"
	@echo ""
	@echo "  SSL/HTTPS:"
	@echo "    make cert              - Renew existing managed TLS certificate"
	@echo "    make cert-init         - Explicit first TLS issuance after DNS/Nginx setup"
	@echo "    make cert-dry-run      - Test renewal without replacing live certificate"
	@echo ""
	@echo "  Shared Management (Uses local .venv):"
	@echo "    make migrate           - Apply migrations locally"
	@echo "    make superuser         - Create superuser locally"
	@echo "    make cache-clear       - Clear Wagtail cache locally"
	@echo "    make db-init-umami     - Manually initialize Umami database (Dev)"

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev-up: dev-start
	@echo "Waiting for containers to initialize..."
	@sleep 2
	$(MAKE) dev-logs

dev-start:
	$(COMPOSE_DEV) up -d

dev-down:
	$(COMPOSE_DEV) down --remove-orphans

dev-logs:
	$(COMPOSE_DEV) logs -f

dev-reset:
	$(call confirm_action,FULL RESET (ALL DATA WILL BE LOST))
	$(COMPOSE_DEV) down -v --remove-orphans
	$(COMPOSE_DEV) up -d

dev-db-refresh:
	$(call confirm_action,REFRESH DJANGO DB (Umami data will be preserved))
	$(COMPOSE_DEV) exec db dropdb -U $(DB_USER) --if-exists $(DB_NAME)
	$(COMPOSE_DEV) exec db createdb -U $(DB_USER) $(DB_NAME)
	@echo "Django development database refreshed."



run:
	$(MANAGE) runserver

# ==============================================================================
# PRODUCTION
# ==============================================================================

prod-up: prod-start
	@echo "Waiting for containers to initialize..."
	@sleep 2
	$(MAKE) prod-logs

prod-start:
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/release.sh

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f

prod-logs-web:
	$(COMPOSE_PROD) logs -f web

prod-logs-dozzle:
	$(COMPOSE_PROD) logs -f dozzle

prod-build:
	APP_IMAGE=homeservice:local RELEASE_REVISION=$$(git rev-parse HEAD) $(COMPOSE_PROD) -f deploy/docker-compose.build.yml build web

prod-migrate:
	$(COMPOSE_PROD) run --rm release

prod-superuser:
	$(DOCKER_EXEC) python manage.py createsuperuser

prod-cache-clear:
	$(DOCKER_EXEC) python manage.py clear_wagtail_cache

prod-shell:
	$(DOCKER_EXEC) python manage.py shell

prod-db-refresh:
	$(call confirm_action,REFRESH PRODUCTION DJANGO DB (Umami data will be preserved))
	$(COMPOSE_PROD) exec db dropdb -U $(DB_USER) --if-exists $(DB_NAME)
	$(COMPOSE_PROD) exec db createdb -U $(DB_USER) $(DB_NAME)
	@echo "Django production database refreshed."

prod-reset:
	$(call confirm_action,FULL PRODUCTION RESET (ALL DATA WILL BE LOST))
	$(COMPOSE_PROD) down -v --remove-orphans
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/release.sh init
	@echo "Full production reset complete."

# ==============================================================================
# BACKUP & MAINTENANCE
# ==============================================================================

prod-db-backup:
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/backup.sh

# ==============================================================================
# SSL / HTTPS
# ==============================================================================

cert:
	@COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/certbot/cert-manage.sh renew

cert-init:
	@COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/certbot/cert-manage.sh init

cert-dry-run:
	@COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/certbot/cert-manage.sh dry-run

# ==============================================================================
# LOG MANAGEMENT & SECURITY (DOZZLE)

# Generates a bcrypt-hashed users.yml file for Dozzle basic auth.
# An explicit password is required; defaults never create production users.
# The resulting file is saved to deploy/dozzle/users.yml.
# Read a strong DOZZLE_PASS interactively and export it; see docs/LOGS.md.
# ==============================================================================
DOZZLE_USER ?= admin
DOZZLE_PASS ?=
DOZZLE_EMAIL ?= admin@gmail.com
DOZZLE_NAME ?= admin_user

dozzle-gen-pass:
	@test -n "$(DOZZLE_PASS)" && test "$(DOZZLE_PASS)" != admin || (echo "Set DOZZLE_PASS to a strong password"; exit 1)
	@mkdir -p deploy/dozzle
	@chmod 700 deploy/dozzle
	@docker run --rm amir20/dozzle:v10.6.3 generate "$(DOZZLE_USER)"  --password "$(DOZZLE_PASS)" --email "$(DOZZLE_EMAIL)" --name "$(DOZZLE_NAME)" > deploy/dozzle/users.yml
	@chmod 600 deploy/dozzle/users.yml
	@echo "Success! Authorization file generated and saved to deploy/dozzle/users.yml"
	@echo "Restart only Dozzle after credential changes; see docs/LOGS.md"

# ==============================================================================
# LOCAL MANAGEMENT
# ==============================================================================

migrate:
	$(MANAGE) migrate

superuser:
	$(MANAGE) createsuperuser

cache-clear:
	$(MANAGE) clear_wagtail_cache

db-init-umami:
	@echo "Initializing Umami database in Dev container..."
	$(COMPOSE_DEV) exec db /docker-entrypoint-initdb.d/init-db.sh

.PHONY: assets test check cert-init cert-dry-run prod-init prod-smoke prod-rollback prod-backup-local prod-tools
assets:
	npm ci
	npm run build

test:
	PYTHONDONTWRITEBYTECODE=1 $(MANAGE) test cms.tests --settings=settings.test
	$(PYTHON) -m unittest discover -s tests -v

check:
	uv lock --check
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(MANAGE) check --settings=settings.test

prod-init:
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/release.sh init

prod-smoke:
	HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/smoke.sh

prod-rollback:
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/release.sh rollback

prod-backup-local:
	COMPOSE_PROJECT_NAME=$(PROJECT_PROD) HOMESERVICE_ENV_FILE=$(HOMESERVICE_ENV_FILE) bash deploy/scripts/backup.sh --local

prod-tools:
	@test -s deploy/dozzle/users.yml || (echo 'Create Dozzle users explicitly first'; exit 1)
	$(COMPOSE_PROD) --profile tools up -d dozzle
