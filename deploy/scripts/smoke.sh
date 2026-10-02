#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
ENV_FILE=${HOMESERVICE_ENV_FILE:-$ROOT/.env}
# SITE_URL is plain configuration, not executable shell.
SITE=${SMOKE_URL:-${SITE_URL:-}}
if [[ -z "$SITE" ]]; then
    SITE=$(sed -n 's/^SITE_URL=//p' "$ENV_FILE" | tail -n 1)
    SITE=${SITE%$'\r'}; SITE=${SITE#\"}; SITE=${SITE%\"}; SITE=${SITE#\'}; SITE=${SITE%\'}
fi
[[ "$SITE" == https://* ]] || { echo 'Set an HTTPS SITE_URL/SMOKE_URL for external smoke verification.' >&2; exit 1; }
response=$(curl --fail --silent --show-error --retry 12 --retry-delay 2 --retry-all-errors --max-time 10 "${SITE%/}/ready/")
printf '%s' "$response" | python3 -c '
import json, os, sys
result = json.load(sys.stdin)
if result.get("status") != "ok":
    sys.exit("Readiness reports unavailable dependencies")
expected = os.getenv("EXPECTED_REVISION")
if expected and result.get("revision") != expected:
    sys.exit("Readiness reports a stale release")
'
curl --fail --silent --show-error --max-time 15 "${SITE%/}/" --output /dev/null
curl --fail --silent --show-error --max-time 15 "${SITE%/}/static/cms/dist/main.css" --output /dev/null
curl --fail --silent --show-error --max-time 15 "${SITE%/}/static/cms/dist/bootstrap.bundle.min.js" --output /dev/null
echo 'HTTPS readiness, homepage and assets passed.'
