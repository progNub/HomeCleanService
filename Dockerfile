FROM node:22.22.0-bookworm-slim AS assets
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY scripts/build-assets.mjs scripts/build-assets.mjs
COPY cms/static/cms/scss cms/static/cms/scss
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.9.26 AS uv
FROM python:3.12.12-slim-bookworm AS python-deps
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-cache

FROM python:3.12.12-slim-bookworm
ARG RELEASE_REVISION=development
LABEL org.opencontainers.image.revision=$RELEASE_REVISION
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" PORT=8000 \
    DJANGO_SETTINGS_MODULE=settings.production DJANGO_LOAD_DOTENV=0 \
    RELEASE_REVISION=$RELEASE_REVISION
RUN useradd --uid 1000 --create-home wagtail \
    && apt-get update && apt-get install --yes --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=python-deps /opt/venv /opt/venv
COPY --chown=wagtail:wagtail manage.py ./
COPY --chown=wagtail:wagtail cms ./cms
COPY --chown=wagtail:wagtail search ./search
COPY --chown=wagtail:wagtail settings ./settings
COPY --chown=wagtail:wagtail locale ./locale
COPY --chown=wagtail:wagtail deploy/entrypoint.sh deploy/worker-entrypoint.sh deploy/release-entrypoint.sh ./deploy/
COPY --from=assets --chown=wagtail:wagtail /src/cms/static/cms/dist ./cms/static/cms/dist
RUN mkdir -p /opt/homeservice/static /app/media /app/staticfiles \
    && chown -R wagtail:wagtail /opt/homeservice /app/media /app/staticfiles
USER wagtail
RUN DJANGO_SETTINGS_MODULE=settings.build python manage.py collectstatic --noinput
EXPOSE 8000
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
