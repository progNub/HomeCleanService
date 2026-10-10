#!/usr/bin/env bash
# Install the certificate renewal timer for the current deployment checkout.
set -Eeuo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
SYSTEMD_DIR=/etc/systemd/system
OPERATIONS_DIR=/etc/homeservice
SERVICE=homeservice-cert-renew.service
TIMER=homeservice-cert-renew.timer

test -x "$ROOT/deploy/certbot/cert-task-runner.sh"
test -f "$ENV_FILE"

install -d -m 0755 "$OPERATIONS_DIR"
install -m 0600 /dev/null "$OPERATIONS_DIR/operations.env"
printf 'COMPOSE_PROJECT_NAME=%s\nHOMESERVICE_ENV_FILE=%s\n' \
    "$PROJECT" "$ENV_FILE" >"$OPERATIONS_DIR/operations.env"

service_tmp=$(mktemp)
trap 'rm -f -- "$service_tmp"' EXIT
sed "s|/opt/homeservice|$ROOT|g" "$ROOT/deploy/systemd/$SERVICE" >"$service_tmp"
install -m 0644 "$service_tmp" "$SYSTEMD_DIR/$SERVICE"
install -m 0644 "$ROOT/deploy/systemd/$TIMER" "$SYSTEMD_DIR/$TIMER"

systemctl daemon-reload
systemctl enable --now "$TIMER"
systemctl --no-pager status "$TIMER"
systemctl --no-pager list-timers "$TIMER"
