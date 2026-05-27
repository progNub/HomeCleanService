#!/bin/bash

# Stop script on error
set -e

echo "--> Running migrations..."
python manage.py migrate --noinput
echo "--> Collecting static files..."
python manage.py collectstatic --noinput --clear
python manage.py compress --force
echo "--> Initializing site data..."
python manage.py init_site

echo "--> Starting Gunicorn..."
exec gunicorn cms.wsgi:application \
    --name homeservice \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --log-level=info \
    --access-logfile - \
    --error-logfile -
