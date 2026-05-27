#!/bin/bash
set -e

# Function to check if a database exists
function database_exists() {
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='$1'" | grep -q 1
}

# Create umami database only if it doesn't exist
if ! database_exists "umami"; then
    echo "Creating database: umami"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE umami;
EOSQL
else
    echo "Database umami already exists, skipping creation."
fi
