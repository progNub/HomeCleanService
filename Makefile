# Project constants
PROJECT_DEV = homeservice-dev
PROJECT_PROD = homeservice-prod

# Docker Compose commands
COMPOSE_DEV = docker compose -p $(PROJECT_DEV) -f deploy/docker-compose.dev.yml
COMPOSE_PROD = docker compose -p $(PROJECT_PROD) -f deploy/docker-compose.yml

# Python and Local Virtual Environment
VENV = .venv
PYTHON = $(VENV)/bin/python
MANAGE = $(PYTHON) manage.py

# Docker Execution command for Production
DOCKER_EXEC = $(COMPOSE_PROD) exec web

.PHONY: help dev-up dev-down dev-logs run prod-up prod-down prod-logs prod-build prod-migrate prod-superuser prod-cache-clear prod-shell migrate superuser cache-clear

# Default target: show help
help:
	@echo "Available commands:"
	@echo "  Development (Infrastructure in Docker + App locally):"
	@echo "    make dev-up            - Start DB and Redis for development"
	@echo "    make dev-down          - Stop development infrastructure"
	@echo "    make dev-logs          - Follow development infrastructure logs"
	@echo "    make run               - Run Django development server locally"
	@echo ""
	@echo "  Production (Full stack in Docker):"
	@echo "    make prod-up           - Build and start the full production stack"
	@echo "    make prod-down         - Stop production stack"
	@echo "    make prod-logs         - Follow all production logs"
	@echo "    make prod-logs-web     - Follow only web container logs"
	@echo "    make prod-build        - Rebuild production web image"
	@echo "    make prod-migrate      - Run migrations inside production container"
	@echo "    make prod-superuser    - Create superuser inside production container"
	@echo "    make prod-cache-clear  - Clear Wagtail cache inside production container"
	@echo "    make prod-shell        - Open Django shell inside production container"
	@echo ""
	@echo "  Backup & Maintenance:"
	@echo "    make prod-db-backup    - Create a database backup (SQL dump)"
	@echo ""
	@echo "  Shared Management (Uses local .venv):"
	@echo "    make migrate           - Apply migrations locally"
	@echo "    make superuser         - Create superuser locally"
	@echo "    make cache-clear       - Clear Wagtail cache locally"
	@echo "    make db-init-umami     - Manually initialize Umami database (Dev)"

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev-up:
	$(COMPOSE_DEV) up -d

dev-down:
	$(COMPOSE_DEV) down --remove-orphans

dev-logs:
	$(COMPOSE_DEV) logs -f

run:
	$(MANAGE) runserver

# ==============================================================================
# PRODUCTION
# ==============================================================================

prod-up:
	$(COMPOSE_PROD) up -d --build

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f

prod-logs-web:
	$(COMPOSE_PROD) logs -f web

prod-build:
	$(COMPOSE_PROD) build

prod-migrate:
	$(DOCKER_EXEC) python manage.py migrate

prod-superuser:
	$(DOCKER_EXEC) python manage.py createsuperuser

prod-cache-clear:
	$(DOCKER_EXEC) python manage.py clear_wagtail_cache

prod-shell:
	$(DOCKER_EXEC) python manage.py shell

# ==============================================================================
# BACKUP & MAINTENANCE
# ==============================================================================

prod-db-backup:
	@mkdir -p backups
	$(COMPOSE_PROD) exec db pg_dump -U homeservice_user homeservice > backups/db_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/ directory."

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
