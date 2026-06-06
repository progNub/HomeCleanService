from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

DEV_INSTALLED_APPS = [
    "debug_toolbar",
    "django_browser_reload",
    "wagtail.contrib.styleguide",
]

DEV_MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]


INSTALLED_APPS += DEV_INSTALLED_APPS
MIDDLEWARE += DEV_MIDDLEWARE

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
