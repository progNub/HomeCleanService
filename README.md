# HomeService - Wagtail CMS Project

This is a professional Wagtail-based CMS project for HomeService.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.12+**
- **Docker & Docker Compose**
- **uv** (fast Python package manager)
- **Node.js 20+** (for frontend assets compilation)
- **Make** (optional, but highly recommended for automation)

## Getting Started (Development)

The recommended way to develop is using a **Hybrid Mode**: infrastructure (Database and Redis) runs in Docker, while the Django application runs locally.

### 1. Initial Setup

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd HomeService
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip install -e .
    npm install
    ```

3.  **Configure environment variables**:
    Create a `.env` file in the root directory and fill it with necessary values (use `.env.example` if provided or copy from the instruction):
    ```env
    DEBUG=True
    DJANGO_SECRET_KEY=your-secret-key
    DB_NAME=homeservice
    DB_USER=homeservice_user
    DB_PASSWORD=homeservice_pass
    # DB_HOST=localhost (default for local development)
    # DB_PORT=5433 (default for dev container)
    ```

### 2. Launch Infrastructure

Start PostgreSQL and Redis in Docker:
```bash
make dev-up
```
*Note: This will start the database on port **5433** and Redis on **6380** to avoid conflicts with other projects.*

### 3. Initialize Database

Run migrations and create an admin user:
```bash
make migrate
make superuser
```

### 4. Run the Application

Start the Django development server:
```bash
make run
```
The site will be available at [http://localhost:8000](http://localhost:8000).

---

## Production Deployment (Docker)

To run the full production stack (Nginx + Gunicorn + Postgres + Redis) inside Docker:

1.  **Start the production stack**:
    ```bash
    make prod-up
    ```

2.  **Initialize production database** (first time only):
    ```bash
    make prod-migrate
    make prod-superuser
    ```

3.  **Logs**:
    View all logs: `make prod-logs`
    View web logs: `make prod-logs-web`

---

## Project Structure & Commands

### Useful Commands

| Command | Description |
| :--- | :--- |
| `make dev-up` | Start local DB and Redis |
| `make dev-down` | Stop local infrastructure |
| `make run` | Start local Django server |
| `make migrate` | Apply migrations locally |
| `make superuser` | Create admin user locally |
| `make cache-clear` | Clear Wagtail cache |
| `make prod-db-backup` | Create a DB backup in `backups/` |
| `make help` | Show all available commands |

### Health Checks & Security
- **Rate Limiting**: Configured at the Nginx level (5 req/s per IP with burst support) to protect against DDoS and brute-force.
- **Security Headers**: Production settings include HSTS, SSL redirect, and secure cookies.
- **Docker Health Checks**: Containers `web` and `db` have health checks configured for better stability.

### Architecture
- **Settings**: Split into `base.py`, `dev.py`, and `production.py`.
- **Database**: PostgreSQL 16 (production) / PostgreSQL 16 in Docker (development).
- **Caching**: Redis with `wagtail-cache` for automatic page invalidation.
- **Frontend**: Sass/Bootstrap compiled via `django-compressor`.

## Localization
The project is configured for Russian (`ru-ru`) by default and supports multiple languages via `wagtail-localize`.
