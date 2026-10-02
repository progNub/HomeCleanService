#!/bin/bash
set -Eeuo pipefail
umask 077

CERT_DIR=/etc/letsencrypt/live/homecleanservice.by
BOOTSTRAP_DIR=/etc/letsencrypt/bootstrap/homecleanservice.by
ACTIVE=/run/homeservice-tls
if [[ -s "$CERT_DIR/fullchain.pem" && -s "$CERT_DIR/privkey.pem" ]]; then
    TARGET=$CERT_DIR
elif [[ "${1:-}" == --refresh-certificates ]]; then
    echo 'Issued certificate/key missing; keeping current Nginx configuration.' >&2
    exit 1
else
    mkdir -p "$BOOTSTRAP_DIR"
    if [[ ! -s "$BOOTSTRAP_DIR/fullchain.pem" || ! -s "$BOOTSTRAP_DIR/privkey.pem" ]]; then
        openssl req -x509 -nodes -newkey rsa:2048 -days 7 \
            -keyout "$BOOTSTRAP_DIR/privkey.pem" -out "$BOOTSTRAP_DIR/fullchain.pem" \
            -subj '/CN=localhost'
    fi
    TARGET=$BOOTSTRAP_DIR
    echo 'Using bootstrap TLS certificate; run make cert-init to issue a trusted one.'
fi
PREVIOUS=$(readlink "$ACTIVE" || true)
ln -sfn "$TARGET" "$ACTIVE"
if ! nginx -t; then
    [[ -z "$PREVIOUS" ]] || ln -sfn "$PREVIOUS" "$ACTIVE"
    exit 1
fi
if [[ "${1:-}" == --refresh-certificates ]]; then
    nginx -s reload
else
    exec nginx -g 'daemon off;'
fi
