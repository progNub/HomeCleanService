"""Same development settings/database as the website, reached inside Docker."""

from .dev import *

# Keep local.py's database name/media, but use the container network address.
DATABASES["default"].update(HOST=ENV_DB_HOST, PORT=ENV_DB_PORT)
