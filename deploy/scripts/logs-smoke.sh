#!/usr/bin/env bash
# Verify the public login and deny anonymous access to actual log streams.
set -Eeuo pipefail
SITE=${LOGS_SMOKE_URL:-https://logs.homecleanservice.by}
[[ "$SITE" == https://* ]] || { echo 'LOGS_SMOKE_URL must use HTTPS.' >&2; exit 1; }
for attempt in {1..15}; do
    login=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 10 "${SITE%/}/login") || login=000
    stream=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 10 "${SITE%/}/api/events/stream") || stream=000
    if [[ "$login" == 200 && "$stream" == 401 ]]; then
        echo 'Dozzle HTTPS login passed; anonymous log stream denied (401).'
        exit 0
    fi
    sleep 2
done
echo "Dozzle smoke failed: login=$login, anonymous stream=$stream (expected 200/401)." >&2
exit 1
