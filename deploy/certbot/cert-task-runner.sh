#!/usr/bin/env bash
# Run a host-only certificate operation and expose its result in Django Tasks.
set -Eeuo pipefail
umask 077

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
export HOMESERVICE_ENV_FILE="$ENV_FILE"
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
MODE=${1:-renew}
case "$MODE" in renew|dry-run) ;; *) echo 'Usage: cert-task-runner.sh [renew|dry-run]' >&2; exit 2;; esac

if [[ -z "${APP_IMAGE:-}" && -s "$ROOT/deploy/.release/current-image" ]]; then
    export APP_IMAGE
    APP_IMAGE=$(<"$ROOT/deploy/.release/current-image")
fi
: "${APP_IMAGE:?No deployed application image is recorded}"

COMPOSE=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/docker-compose.yml" -f "$ROOT/deploy/docker-compose.prod.yml")
"${COMPOSE[@]}" config --quiet
"${COMPOSE[@]}" ps --status running --services | grep -qx web || {
    echo 'The production web container must be running to track certificate tasks.' >&2
    exit 1
}

mkdir -p "$ROOT/.runtime"
LOG=$(mktemp "$ROOT/.runtime/cert-task-XXXXXXXX.log")
TASK_ID=""
FINALIZED=0
cleanup() {
    status=$?
    if [[ "$FINALIZED" == 0 && -n "$TASK_ID" ]]; then
        printf '\nCertificate task runner stopped before completion (exit %s).\n' "$status" >>"$LOG"
        "${COMPOSE[@]}" exec -T web python manage.py certificate_task finish "$TASK_ID" --status failed <"$LOG" || true
    fi
    rm -f -- "$LOG"
}
trap cleanup EXIT

TASK_ID=$("${COMPOSE[@]}" exec -T web python manage.py certificate_task enqueue --mode "$MODE")
"${COMPOSE[@]}" exec -T web python manage.py certificate_task claim "$TASK_ID"

set +e
COMPOSE_PROJECT_NAME="$PROJECT" HOMESERVICE_ENV_FILE="$ENV_FILE" \
    bash "$ROOT/deploy/certbot/cert-manage.sh" "$MODE" >"$LOG" 2>&1
operation_status=$?
set -e

if [[ "$operation_status" == 0 ]]; then
    result_status=successful
else
    result_status=failed
fi

"${COMPOSE[@]}" exec -T web python manage.py certificate_task finish "$TASK_ID" --status "$result_status" <"$LOG"
FINALIZED=1
cat "$LOG"
exit "$operation_status"
