#!/usr/bin/env bash
# Never overwrites an existing database or media tree; promotion is an operator step.
set -Eeuo pipefail
umask 077
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
export HOMESERVICE_ENV_FILE="$ENV_FILE"
PROJECT=${COMPOSE_PROJECT_NAME:-homeservice-prod}
BUNDLE= DATABASE= MEDIA_TARGET= DUMP=db.dump
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backup) BUNDLE=${2:?}; shift 2;;
        --database) DATABASE=${2:?}; shift 2;;
        --media-dir) MEDIA_TARGET=${2:?}; shift 2;;
        --umami) DUMP=umami.dump; shift;;
        *) echo 'Usage: restore.sh --backup DIR --database NEW_NAME [--media-dir EMPTY_DIR] [--umami]' >&2; exit 2;;
    esac
done
[[ -d "$BUNDLE" && "$DATABASE" =~ ^[a-zA-Z_][a-zA-Z0-9_]{0,62}$ ]] || { echo 'An existing backup directory and explicit new database name are required.' >&2; exit 2; }
BUNDLE=$(cd "$BUNDLE" && pwd)
[[ -f "$BUNDLE/$DUMP" && -f "$BUNDLE/media.tar.gz" && -f "$BUNDLE/SHA256SUMS" ]] || { echo 'Incomplete backup bundle.' >&2; exit 1; }
awk 'NF != 2 || $1 !~ /^[a-f0-9]+$/ || length($1) != 64 || $2 !~ /^(db[.]dump|umami[.]dump|media[.]tar[.]gz)$/ { exit 1 }' "$BUNDLE/SHA256SUMS"
awk -v dump="$DUMP" '$2 == dump { found=1 } END { exit !found }' "$BUNDLE/SHA256SUMS"
awk '$2 == "media.tar.gz" { found=1 } END { exit !found }' "$BUNDLE/SHA256SUMS"
(cd "$BUNDLE" && sha256sum --strict -c SHA256SUMS)
if [[ -n "$MEDIA_TARGET" ]]; then
    [[ ! -e "$MEDIA_TARGET" || ( -d "$MEDIA_TARGET" && -z "$(ls -A "$MEDIA_TARGET")" ) ]] || { echo 'Media destination must be absent or empty.' >&2; exit 1; }
    tar -tzf "$BUNDLE/media.tar.gz" | awk '/^\// || /(^|\/)\.\.(\/|$)/ { bad=1 } END { exit bad }'
fi
COMPOSE=(docker compose --env-file "$ENV_FILE" -p "$PROJECT" -f "$ROOT/deploy/docker-compose.yml")
# createdb fails if the name already exists; never use --clean or dropdb.
"${COMPOSE[@]}" exec -T db sh -ec 'exec createdb -U "$POSTGRES_USER" "$1"' sh "$DATABASE"
if ! "${COMPOSE[@]}" exec -T db sh -ec 'exec pg_restore --exit-on-error --single-transaction --no-owner --no-acl -U "$POSTGRES_USER" -d "$1"' sh "$DATABASE" <"$BUNDLE/$DUMP"; then
    echo "Restore failed; new database $DATABASE retained for inspection. No existing database was replaced." >&2
    exit 1
fi
if [[ -n "$MEDIA_TARGET" ]]; then
    mkdir -p "$MEDIA_TARGET"
    tar -xzf "$BUNDLE/media.tar.gz" --no-same-owner --no-same-permissions -C "$MEDIA_TARGET"
fi
echo "Restored to new database $DATABASE. Validate before any production promotion."
