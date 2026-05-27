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

# Check for existing renewal configuration (indicates real certificates)
# We also check if the certificate is not a dummy one
IS_DUMMY=0
if $COMPOSE_SSL run --rm --entrypoint "openssl x509 -noout -subject -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem" certbot 2>/dev/null | grep -q "CN = localhost"; then
    IS_DUMMY=1
fi

RENEWAL_CONF_EXISTS=0
if $COMPOSE_SSL run --rm --entrypoint "ls /etc/letsencrypt/renewal/$DOMAIN.conf" certbot >/dev/null 2>&1; then
    RENEWAL_CONF_EXISTS=1
fi

if [ "$RENEWAL_CONF_EXISTS" -eq 1 ] && [ "$IS_DUMMY" -eq 0 ]; then
    echo "Real certificates found. Attempting to renew..."
    if ! $COMPOSE_SSL run --rm certbot renew; then
        echo "Renewal failed. Trying to re-obtain certificates..."
        $COMPOSE_SSL run --rm --entrypoint \
            "certbot certonly --webroot -w /var/www/certbot \
            --email $CERT_EMAIL --agree-tos --no-eff-email --force-renewal \
            -d $DOMAIN -d www.$DOMAIN -d stats.$DOMAIN" certbot
    fi
else
    echo "Real certificates not found (only dummy or none). Requesting new ones from Let's Encrypt..."
    # If dummy or broken directory exists, we might need to remove it or use --force-renewal
    # Cleaning up dummy/broken directory to avoid "live directory exists" error
    $COMPOSE_SSL run --rm --entrypoint "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

    $COMPOSE_SSL run --rm --entrypoint \
        "certbot certonly --webroot -w /var/www/certbot \
        --email $CERT_EMAIL --agree-tos --no-eff-email \
        -d $DOMAIN -d www.$DOMAIN -d stats.$DOMAIN" certbot
fi

echo "Reloading Nginx..."
$COMPOSE_PROD exec nginx nginx -s reload

echo "SSL task completed successfully!"
