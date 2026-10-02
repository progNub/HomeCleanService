#!/bin/bash

# Stop script on error
set -e

# Management/release commands must not accidentally start the web server.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

echo "--> Starting Gunicorn..."
exec gunicorn cms.wsgi:application \
    --name homeservice \
    --bind 0.0.0.0:$PORT \
    --workers "${WEB_CONCURRENCY:-3}" \
    --log-level=info \
    --access-logfile - \
    --error-logfile -
