#!/bin/sh
set -eu
python manage.py check --deploy --fail-level WARNING
python manage.py migrate --noinput
# Keep old hashed assets so requests from the previous release remain valid.
# Runtime templates use the image's manifest; Nginx serves the shared directory.
cp -R /opt/homeservice/static/. /app/staticfiles/
python manage.py clear_wagtail_cache
