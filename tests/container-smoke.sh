#!/usr/bin/env bash
# Isolated production-image integration; never uses application .env or host ports.
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
: "${HOMESERVICE_TEST_IMAGE:?Set HOMESERVICE_TEST_IMAGE to an already-built app image}"
PREFIX="homeservice-smoke-$(date +%s)-$$-$RANDOM"
NETWORK="$PREFIX-network"
MEDIA="$PREFIX-media"
STATIC="$PREFIX-static"
NGINX_IMAGE="$PREFIX-nginx:local"
PG_IMAGE=postgres:16-alpine@sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685
REDIS_IMAGE=redis:alpine@sha256:ad0a6eff0a40304ab1ab4f50f0dc192d82b071e1094eac961bcb6106092f8a4e
NGINX_BASE=nginx@sha256:5aca99593157f4ae539a5dec1092a0ad8762f8e2eb1789085a13a0f5622369f6
CONTAINERS=()
VOLUMES=()
NETWORK_CREATED=0
IMAGE_CREATED=0
cleanup() {
    local status=$?
    trap - EXIT
    if [[ $status != 0 ]]; then
        for name in "${CONTAINERS[@]}"; do docker logs --tail 40 "$name" >&2 || true; done
    fi
    for name in "${CONTAINERS[@]}"; do docker rm -fv "$name" >/dev/null || true; done
    for name in "${VOLUMES[@]}"; do docker volume rm "$name" >/dev/null || true; done
    [[ "$NETWORK_CREATED" != 1 ]] || docker network rm "$NETWORK" >/dev/null || true
    [[ "$IMAGE_CREATED" != 1 ]] || docker image rm "$NGINX_IMAGE" >/dev/null || true
    exit "$status"
}
trap cleanup EXIT
docker image inspect "$HOMESERVICE_TEST_IMAGE" >/dev/null
REVISION=$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$HOMESERVICE_TEST_IMAGE")
docker network create --internal "$NETWORK" >/dev/null
NETWORK_CREATED=1
docker volume create "$MEDIA" >/dev/null
VOLUMES+=("$MEDIA")
docker volume create "$STATIC" >/dev/null
VOLUMES+=("$STATIC")

# COPY avoids host bind mounts, including Docker Desktop /tmp sharing differences.
docker build --quiet --tag "$NGINX_IMAGE" --build-arg "NGINX_BASE=$NGINX_BASE" -f - . <<'DOCKERFILE'
ARG NGINX_BASE
FROM ${NGINX_BASE}
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/nginx/entrypoint/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
DOCKERFILE
IMAGE_CREATED=1

PG="$PREFIX-postgres"
REDIS="$PREFIX-redis"
WEB="$PREFIX-web"
NGINX="$PREFIX-nginx"
docker run -d --name "$PG" --network "$NETWORK" --network-alias db \
    -e POSTGRES_DB=smoke -e POSTGRES_USER=smoke -e POSTGRES_PASSWORD=synthetic-smoke-password "$PG_IMAGE" >/dev/null
CONTAINERS+=("$PG")
docker run -d --name "$REDIS" --network "$NETWORK" --network-alias redis "$REDIS_IMAGE" >/dev/null
CONTAINERS+=("$REDIS")
ready=0
for attempt in {1..60}; do
    if docker exec "$PG" pg_isready -U smoke -d smoke >/dev/null 2>&1 && docker exec "$REDIS" redis-cli ping >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
done
[[ "$ready" == 1 ]] || { echo 'Isolated database/cache readiness failed.' >&2; exit 1; }

APP_ENV=(
    -e DJANGO_SETTINGS_MODULE=settings.production -e DJANGO_LOAD_DOTENV=0
    -e DJANGO_SECRET_KEY=synthetic-integration-only-Key-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ
    -e ALLOWED_HOSTS=homecleanservice.by -e SITE_URL=https://homecleanservice.by
    -e DB_NAME=smoke -e DB_USER=smoke -e DB_PASSWORD=synthetic-smoke-password
    -e DB_HOST=db -e DB_PORT=5432 -e REDIS_URL=redis://redis:6379/0
    -e SECURE_SSL_REDIRECT=True -e TELEGRAM_BOT_TOKEN= -e TELEGRAM_NOTIFICATIONS_CHAT_ID= -e TELEGRAM_LOGS_CHAT_ID=
)
MOUNTS=(--mount "type=volume,source=$MEDIA,target=/app/media" --mount "type=volume,source=$STATIC,target=/app/staticfiles")
docker run --rm --user 0 --network "$NETWORK" "${MOUNTS[@]}" --entrypoint python "$HOMESERVICE_TEST_IMAGE" \
    -c 'import os; os.chown("/app/media",1000,1000); os.chown("/app/staticfiles",1000,1000)'
docker run --rm --network "$NETWORK" "${APP_ENV[@]}" "${MOUNTS[@]}" \
    --entrypoint /app/deploy/release-entrypoint.sh "$HOMESERVICE_TEST_IMAGE"
docker run --rm --network "$NETWORK" "${APP_ENV[@]}" "${MOUNTS[@]}" \
    --entrypoint python "$HOMESERVICE_TEST_IMAGE" manage.py init_site --content-only
# Umami DNS is required by Nginx config; this alias does not test analytics.
docker run -d --name "$WEB" --network "$NETWORK" --network-alias web --network-alias umami \
    "${APP_ENV[@]}" "${MOUNTS[@]}" "$HOMESERVICE_TEST_IMAGE" >/dev/null
CONTAINERS+=("$WEB")
docker run -d --name "$NGINX" --network "$NETWORK" \
    --mount "type=volume,source=$MEDIA,target=/app/media,readonly" \
    --mount "type=volume,source=$STATIC,target=/app/staticfiles,readonly" "$NGINX_IMAGE" >/dev/null
CONTAINERS+=("$NGINX")

# -k applies only to the isolated bootstrap self-signed certificate in this test.
CURL=(docker exec "$NGINX" curl --silent --show-error --fail --insecure --connect-timeout 2 --max-time 5 --noproxy '*' --resolve homecleanservice.by:443:127.0.0.1)
ready=0
for attempt in {1..60}; do
    if response=$("${CURL[@]}" https://homecleanservice.by/ready/ 2>/dev/null); then ready=1; break; fi
    sleep 1
done
[[ "$ready" == 1 ]] || { echo 'Isolated HTTPS readiness failed.' >&2; exit 1; }
EXPECTED_REVISION="$REVISION" python3 -c 'import json,os,sys; value=json.loads(sys.argv[1]); sys.exit(0 if value.get("status")=="ok" and value.get("revision")==os.environ["EXPECTED_REVISION"] else 1)' "$response"
docker exec "$NGINX" nginx -t
headers=$("${CURL[@]}" --head https://homecleanservice.by/)
printf '%s' "$headers" | grep -qi '^Strict-Transport-Security:'
printf '%s' "$headers" | grep -qi '^Content-Security-Policy:'
printf '%s' "$headers" | grep -qi '^X-Content-Type-Options: nosniff'
homepage=$("${CURL[@]}" https://homecleanservice.by/)
[[ "$homepage" == *'<html'* && "$homepage" == *'/static/'* ]] || { echo 'Homepage HTML is incomplete.' >&2; exit 1; }
"${CURL[@]}" https://homecleanservice.by/static/cms/dist/main.css --output /dev/null
"${CURL[@]}" https://homecleanservice.by/static/cms/dist/bootstrap.bundle.min.js --output /dev/null
redirect=$(docker exec "$NGINX" curl --silent --show-error --connect-timeout 2 --max-time 5 --noproxy '*' --head --resolve homecleanservice.by:80:127.0.0.1 http://homecleanservice.by/)
printf '%s' "$redirect" | grep -q '301 Moved Permanently'
printf '%s' "$redirect" | grep -qi '^Location: https://homecleanservice.by/'
echo "Container integration passed: migrations, content, DB/Redis readiness, revision $REVISION, HTTPS homepage/assets/security headers, HTTP redirect."
