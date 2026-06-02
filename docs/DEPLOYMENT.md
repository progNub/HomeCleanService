# Deployment Guide

This project is prepared for deployment using **Docker**, **PostgreSQL**, and **Gunicorn**.

## 1. Environment Variables Setup

You need to create a `.env` file in the project root with the following parameters:

```env
# Core Django Settings
DJANGO_SECRET_KEY=your_secret_key
DEBUG=False
SITE_URL=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Settings (PostgreSQL)
DB_NAME=homeservice
DB_USER=homeservice_user
DB_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432

# Superuser Settings (for automatic creation via init_site)
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=secure_password

# Contact Information
CONTACT_PHONE=+375XXXXXXXXX
CONTACT_EMAIL=info@yourdomain.com
CONTACT_ADDRESS=Your address
```

## 2. Deployment via Docker Compose

All production configuration files are located in the `deploy/` folder. It is recommended to use the `Makefile` to automate commands.

### Launch in Production:
```bash
make prod-up
```
This will start the full stack: **Nginx**, **Web (Django/Gunicorn)**, **PostgreSQL**, **Redis**, and **Umami**.

### Initialization (first run only):
```bash
make prod-migrate
make prod-superuser
```

### Updating the Project:
```bash
git pull
make prod-up
```

---

## 3. Architecture and Tools

1. **Database**: The project uses **PostgreSQL 16**. In production, data is persisted in Docker volumes.
2. **Caching**: **Redis** is used for page caching and performance improvement.
3. **SSL (HTTPS)**: SSL setup is handled via scripts in `deploy/certbot/`. Use `make cert` to manage certificates.
4. **Analytics**: **Umami** is included in the stack. Setup instructions are in `deploy/docs/umami.md`.

## 4. Site Initialization (init_site)

Upon container start or manually via `make prod-migrate` (if `entrypoint.sh` is configured), the `python manage.py init_site` command may be executed. It performs the following:
1. Creates a superuser based on `.env`.
2. Creates the page structure (HomePage, LegalPages, Portfolio).
3. Configures basic global settings (Contacts, Social Networks).

## 5. Maintenance

- **Database Backup**: `make prod-db-backup` (saves a dump to the `backups/` folder).
- **Logs**: `make prod-logs` or `make prod-logs-web`.
- **Clear Cache**: `make prod-cache-clear`.
