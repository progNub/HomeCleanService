from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# SECURITY SETTINGS
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy setting for HTTPS detection
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not CSRF_TRUSTED_ORIGINS or CSRF_TRUSTED_ORIGINS == [""]:
    # Fallback or empty if not provided
    CSRF_TRUSTED_ORIGINS = []

# ==============================================================================
# CACHING SETTINGS (Redis & Wagtail Cache)
# ==============================================================================
CACHE_TIMEOUT = ENV_CACHE_TIMEOUT

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ENV_REDIS_URL,
        # TTL for cache entries stored via Django cache API (cache.set, template fragment cache, etc.).
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Wagtail-cache configuration
WAGTAIL_CACHE = True
WAGTAIL_CACHE_HEADER = "X-Wagtail-Cache"

# Cache timeout and key prefix
# TTL for full-page HTTP responses cached by Update/Fetch cache middleware.
CACHE_MIDDLEWARE_SECONDS = CACHE_TIMEOUT
CACHE_MIDDLEWARE_KEY_PREFIX = "homeservice"
# ==============================================================================

try:
    from .local import *
except ImportError:
    pass
