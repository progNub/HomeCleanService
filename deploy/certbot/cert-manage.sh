#!/bin/bash

# Script to manage Certbot SSL certificates

set -e

DOMAIN="homecleanservice.by"
# Try to get email from .env
CERT_EMAIL=$(grep CERTBOT_EMAIL .env | cut -d '=' -f2 || echo "")

if [ -z "$CERT_EMAIL" ]; then
    echo "Error: CERTBOT_EMAIL not found in .env file."
    exit 1
fi

COMPOSE_SSL="docker compose -p homeservice-prod -f deploy/certbot/docker-compose.yml"
COMPOSE_PROD="docker compose -p homeservice-prod -f deploy/docker-compose.yml"

echo "Checking SSL certificates for $DOMAIN..."

# Check for existing certificates
if $COMPOSE_SSL run --rm --entrypoint "ls /etc/letsencrypt/live/$DOMAIN" certbot >/dev/null 2>&1; then
    echo "Certificates found. Attempting to renew..."
    $COMPOSE_SSL run --rm certbot renew
else
    echo "Certificates not found. Requesting new ones..."
    $COMPOSE_SSL run --rm --entrypoint \
        "certbot certonly --webroot -w /var/www/certbot \
        --email $CERT_EMAIL --agree-tos --no-eff-email \
        -d $DOMAIN -d www.$DOMAIN -d stats.$DOMAIN" certbot
fi

echo "Reloading Nginx..."
$COMPOSE_PROD exec nginx nginx -s reload

echo "SSL task completed successfully!"
