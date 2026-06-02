#!/bin/bash

# Script to manage Certbot SSL certificates

set -e

DOMAIN="homecleanservice.by"
# Try to get settings from .env
CERT_EMAIL=$(grep CERTBOT_EMAIL .env | cut -d '=' -f2 || echo "")
CERT_DOMAINS_STR=$(grep CERTBOT_DOMAINS .env | cut -d '=' -f2 || echo "$DOMAIN,www.$DOMAIN,stats.$DOMAIN,logs.$DOMAIN")

if [ -z "$CERT_EMAIL" ]; then
    echo "Error: CERTBOT_EMAIL not found in .env file."
    exit 1
fi

# Convert comma-separated domains to Certbot -d flags
IFS=',' read -ra ADDR <<< "$CERT_DOMAINS_STR"
D_FLAGS=""
for i in "${ADDR[@]}"; do
    D_FLAGS="$D_FLAGS -d $i"
done

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
    echo "Real certificates found. Expanding certificate to include new domains if necessary..."
    $COMPOSE_SSL run --rm --entrypoint \
        "certbot certonly --webroot -w /var/www/certbot \
        --email $CERT_EMAIL --agree-tos --no-eff-email --expand \
        --cert-name $DOMAIN \
        $D_FLAGS" certbot
else
    echo "Real certificates not found (only dummy or none). Requesting new ones from Let's Encrypt..."
    # If dummy or broken directory exists, we might need to remove it or use --force-renewal
    # Cleaning up dummy/broken directory to avoid "live directory exists" or suffix "-0001" errors
    # We remove any potential conflicting lineages to ensure a clean request
    $COMPOSE_SSL run --rm --entrypoint "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf /etc/letsencrypt/live/$DOMAIN-0001 /etc/letsencrypt/archive/$DOMAIN-0001 /etc/letsencrypt/renewal/$DOMAIN-0001.conf" certbot

    $COMPOSE_SSL run --rm --entrypoint \
        "certbot certonly --webroot -w /var/www/certbot \
        --email $CERT_EMAIL --agree-tos --no-eff-email \
        --cert-name $DOMAIN \
        $D_FLAGS" certbot
fi

echo "Reloading Nginx..."
$COMPOSE_PROD exec nginx nginx -s reload

echo "SSL task completed successfully!"
