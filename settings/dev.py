from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")
# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

INSTALLED_APPS.append("wagtail.contrib.styleguide")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================================================================
# CACHING SETTINGS (Local Memory)
# ==============================================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

WAGTAIL_CACHE = True
WAGTAIL_CACHE_HEADER = "X-Wagtail-Cache"
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
# ==============================================================================


try:
    from .local import *
except ImportError:
    pass
