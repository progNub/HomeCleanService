#!/bin/bash
set -e

DOMAIN="homecleanservice.by"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
CERT_FILE="$CERT_DIR/fullchain.pem"
KEY_FILE="$CERT_DIR/privkey.pem"

if [ ! -f "$CERT_FILE" ]; then
    echo "--> SSL certificates not found. Generating dummy certificates to allow Nginx to start..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/CN=localhost"
    echo "--> Dummy certificates generated."
else
    echo "--> SSL certificates found."
fi

echo "--> Starting Nginx..."
exec nginx -g "daemon off;"
