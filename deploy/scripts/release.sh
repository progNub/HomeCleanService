#!/usr/bin/env bash
# Deploy an already-built immutable image. Run from the exact checked-out revision.
set -Eeuo pipefail
umask 077
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
export HOMESERVICE_ENV_FILE="$ENV_FILE"
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
MODE=${1:-deploy}
case "$MODE" in deploy|rollback|init) ;; *) echo 'Usage: release.sh [deploy|rollback|init]' >&2; exit 2;; esac
: "${APP_IMAGE:?Set APP_IMAGE to the tested image digest}"
[[ "$APP_IMAGE" =~ @sha256:[a-f0-9]{64}$ || "${ALLOW_LOCAL_IMAGE:-0}" == 1 ]] || {
    echo 'APP_IMAGE must be pinned by sha256 digest (ALLOW_LOCAL_IMAGE=1 for local testing only).' >&2; exit 1;
}
export APP_IMAGE
STATE="$ROOT/deploy/.release"
mkdir -p "$STATE"
exec 9>"$STATE/release.lock"
flock -n 9 || { echo 'Another release is running.' >&2; exit 1; }
COMPOSE=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/docker-compose.yml")
"${COMPOSE[@]}" config --quiet
docker image inspect "$APP_IMAGE" >/dev/null 2>&1 || docker pull "$APP_IMAGE"
IMAGE_REVISION=$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$APP_IMAGE")
CHECKOUT_REVISION=$(git rev-parse HEAD)
EXPECTED_REVISION=${RELEASE_REVISION:-$CHECKOUT_REVISION}
[[ ( "$IMAGE_REVISION" == "$EXPECTED_REVISION" && "$CHECKOUT_REVISION" == "$EXPECTED_REVISION" ) || "${ALLOW_LOCAL_IMAGE:-0}" == 1 ]] || {
    echo 'Image revision does not match the checked-out release.' >&2; exit 1;
}
if [[ "$MODE" == rollback && "${ROLLBACK_DB_COMPATIBLE:-0}" != 1 ]]; then
    echo 'Rollback needs ROLLBACK_DB_COMPATIBLE=1 after verifying schema compatibility; it never reverses migrations.' >&2
    exit 1
fi
"${COMPOSE[@]}" up -d --wait --wait-timeout 120 db redis
# Verify the image and shared-directory ownership before stopping live writers.
"${COMPOSE[@]}" run --rm --no-deps --entrypoint python release manage.py check --deploy --fail-level WARNING
"${COMPOSE[@]}" run --rm --no-deps --entrypoint sh release -ec 'test -w /app/media && test -w /app/staticfiles'
PREVIOUS_IMAGE=""
WEB_ID=$("${COMPOSE[@]}" ps -q web)
if [[ -n "$WEB_ID" ]]; then
    PREVIOUS_IMAGE=$(docker inspect --format '{{.Config.Image}}' "$WEB_ID")
fi
MIGRATION_STARTED=0
on_error() {
    status=$?
    if [[ "$MIGRATION_STARTED" == 0 && -n "$PREVIOUS_IMAGE" ]]; then
        "${COMPOSE[@]}" start web worker || true
    fi
    echo "Release failed (migration started: $MIGRATION_STARTED). See docs/DEPLOYMENT.md; previous image: $PREVIOUS_IMAGE" >&2
    exit "$status"
}
trap on_error ERR
# Small single-host site: explicit maintenance window avoids old workers writing
# against a changing schema and makes the database/media snapshot consistent.
"${COMPOSE[@]}" stop web worker
if [[ "$MODE" != init ]]; then
    COMPOSE_PROJECT_NAME="$PROJECT" bash "$ROOT/deploy/scripts/backup.sh" --local
fi
if [[ "$MODE" != rollback ]]; then
    MIGRATION_STARTED=1
    "${COMPOSE[@]}" run --rm --no-deps release
else
    MIGRATION_STARTED=1
    "${COMPOSE[@]}" run --rm --no-deps --entrypoint sh release -ec 'cp -R /opt/homeservice/static/. /app/staticfiles/; python manage.py clear_wagtail_cache'
fi
"${COMPOSE[@]}" up -d --no-deps --wait --wait-timeout 120 web worker
"${COMPOSE[@]}" up -d umami nginx
# Docker DNS can retain the old web address until Nginx reloads.
"${COMPOSE[@]}" exec -T nginx nginx -t
"${COMPOSE[@]}" exec -T nginx nginx -s reload
if [[ "$MODE" != init ]]; then
    EXPECTED_REVISION="$IMAGE_REVISION" bash "$ROOT/deploy/scripts/smoke.sh"
fi
printf '%s\n' "$PREVIOUS_IMAGE" >"$STATE/previous-image"
printf '%s\n' "$APP_IMAGE" >"$STATE/current-image"
printf '%s\n' "$IMAGE_REVISION" >"$STATE/current-revision"
trap - ERR
echo "Release completed: $IMAGE_REVISION"
if [[ "$MODE" == init ]]; then
    echo 'Bootstrap complete. Explicitly initialize site content, issue TLS certificate, then run make prod-smoke.'
fi
