#!/usr/bin/env bash
# A successful default invocation includes encryption and scp completion.
set -Eeuo pipefail
umask 077
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
export HOMESERVICE_ENV_FILE="$ENV_FILE"
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
BACKUP_DIR=${BACKUP_DIR:-$ROOT/backups}
MEDIA_DIR=${MEDIA_DIR:-$ROOT/media}
LOCAL=0
case "${1:-}" in '') ;; --local) LOCAL=1;; *) echo 'Usage: backup.sh [--local]' >&2; exit 2;; esac
if [[ -z "${BACKUP_GPG_RECIPIENT:-}" || -z "${BACKUP_REMOTE_DIR:-}" ]]; then
    if [[ "$LOCAL" != 1 || -n "${BACKUP_GPG_RECIPIENT:-}${BACKUP_REMOTE_DIR:-}" ]]; then
        echo 'Set BACKUP_GPG_RECIPIENT and BACKUP_REMOTE_DIR, or use --local for a local release snapshot.' >&2
        exit 1
    fi
else
    [[ "$BACKUP_REMOTE_DIR" =~ ^[a-zA-Z0-9_.@-]+:/[a-zA-Z0-9_./-]+$ ]] || { echo 'BACKUP_REMOTE_DIR must be user@host:/absolute/path (no spaces).' >&2; exit 1; }
    command -v gpg >/dev/null
    command -v scp >/dev/null
fi
[[ -d "$MEDIA_DIR" ]] || { echo 'Media directory does not exist.' >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
BACKUP_DIR=$(cd "$BACKUP_DIR" && pwd)
chmod 700 "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.backup.lock"
flock -n 9 || { echo 'Backup already running.' >&2; exit 1; }
WORK=$(mktemp -d "$BACKUP_DIR/.incomplete-XXXXXXXX")
trap 'echo "Backup incomplete; diagnostic files retained in $WORK" >&2' ERR
COMPOSE=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/docker-compose.yml")
"${COMPOSE[@]}" exec -T db sh -ec 'exec pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" "$POSTGRES_DB"' >"$WORK/db.dump"
FILES=(db.dump media.tar.gz)
if [[ "${BACKUP_UMAMI:-1}" == 1 ]]; then
    "${COMPOSE[@]}" exec -T db sh -ec 'exec pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" umami' >"$WORK/umami.dump"
    FILES+=(umami.dump)
fi
tar -czf "$WORK/media.tar.gz" -C "$MEDIA_DIR" .
(cd "$WORK" && sha256sum "${FILES[@]}" >SHA256SUMS)
if [[ -n "${BACKUP_GPG_RECIPIENT:-}" ]]; then
    tar -czf - -C "$WORK" "${FILES[@]}" SHA256SUMS |
        gpg --batch --encrypt --recipient "$BACKUP_GPG_RECIPIENT" --output "$WORK/backup.tar.gz.gpg"
    scp -B -o StrictHostKeyChecking=yes "$WORK/backup.tar.gz.gpg" \
        "$BACKUP_REMOTE_DIR/homeservice-$(date -u +%Y%m%dT%H%M%SZ)-${WORK##*-}.tar.gz.gpg"
fi
FINAL="$BACKUP_DIR/homeservice-$(date -u +%Y%m%dT%H%M%SZ)-${WORK##*-}"
mv "$WORK" "$FINAL"
trap - ERR
echo "Backup completed: $FINAL"
