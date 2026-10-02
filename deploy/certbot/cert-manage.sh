#!/usr/bin/env bash
# Initial issuance is explicit; renew never removes or replaces a lineage.
set -Eeuo pipefail
umask 077
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
export HOMESERVICE_ENV_FILE="$ENV_FILE"
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
MODE=${1:-renew}
case "$MODE" in init|renew|dry-run) ;; *) echo 'Usage: cert-manage.sh [init|renew|dry-run]' >&2; exit 2;; esac
mkdir -p "$ROOT/.runtime"
exec 9>"$ROOT/.runtime/cert.lock"
flock -n 9 || { echo 'Certificate operation already running.' >&2; exit 1; }

# Read only these plain dotenv values; never execute an environment file as shell.
dotenv() {
    local value
    value=$(sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1)
    value=${value%$'\r'}
    value=${value#\"}; value=${value%\"}
    value=${value#\'}; value=${value%\'}
    printf '%s' "$value"
}
DOMAIN=homecleanservice.by
SSL=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/certbot/docker-compose.yml")
PROD=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/docker-compose.yml")
case "$MODE" in
    init)
        EMAIL=${CERTBOT_EMAIL:-$(dotenv CERTBOT_EMAIL)}
        DOMAINS=${CERTBOT_DOMAINS:-$(dotenv CERTBOT_DOMAINS)}
        DOMAINS=${DOMAINS:-homecleanservice.by,www.homecleanservice.by,stats.homecleanservice.by,logs.homecleanservice.by}
        [[ -n "$EMAIL" ]] || { echo 'CERTBOT_EMAIL is required for initial issuance.' >&2; exit 1; }
        FLAGS=()
        IFS=, read -ra NAMES <<< "$DOMAINS"
        for name in "${NAMES[@]}"; do
            [[ "$name" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || { echo 'Invalid CERTBOT_DOMAINS value.' >&2; exit 1; }
            FLAGS+=(-d "$name")
        done
        "${SSL[@]}" run --rm --entrypoint sh certbot -ec '
            live=/etc/letsencrypt/live/homecleanservice.by
            renewal=/etc/letsencrypt/renewal/homecleanservice.by.conf
            if [ -e "$live" ] && [ ! -f "$renewal" ]; then
                echo "Unmanaged certificate lineage exists. Back up and inspect it; see deploy/docs/ssl.md." >&2
                exit 1
            fi'
        "${SSL[@]}" run --rm certbot certonly --non-interactive --webroot -w /var/www/certbot \
            --email "$EMAIL" --agree-tos --no-eff-email --expand --cert-name "$DOMAIN" "${FLAGS[@]}"
        ;;
    renew|dry-run)
        "${SSL[@]}" run --rm --entrypoint sh certbot -ec \
            'test -f /etc/letsencrypt/renewal/homecleanservice.by.conf || { echo "No renewal configuration; run cert-manage.sh init first." >&2; exit 1; }'
        FLAGS=()
        [[ "$MODE" != dry-run ]] || FLAGS+=(--dry-run)
        "${SSL[@]}" run --rm certbot renew --non-interactive --cert-name "$DOMAIN" "${FLAGS[@]}"
        ;;
esac
if [[ "$MODE" != dry-run ]]; then
    "${PROD[@]}" exec -T nginx /entrypoint.sh --refresh-certificates
fi
echo "Certificate operation completed: $MODE"
