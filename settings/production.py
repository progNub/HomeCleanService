from ipaddress import ip_network
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# Fail before connecting to services. Do not include secret values in errors.
for setting_name in (
    "DJANGO_SECRET_KEY",
    "ALLOWED_HOSTS",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "REDIS_URL",
    "SITE_URL",
):
    if not os.getenv(setting_name, "").strip():
        raise ImproperlyConfigured(f"{setting_name} is required in production")
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be a strong random production secret")
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list explicit production hosts")
if not ENV_SITE_URL.startswith("https://") or not urlsplit(ENV_SITE_URL).hostname:
    raise ImproperlyConfigured("SITE_URL must be an absolute HTTPS URL")
for network in TRUSTED_PROXY_CIDRS:
    try:
        ip_network(network)
    except ValueError as exc:
        raise ImproperlyConfigured("TRUSTED_PROXY_CIDRS contains an invalid network") from exc

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REDIRECT_EXEMPT = [r"^health/$", r"^ready/$"]

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# SECURITY SETTINGS
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy setting for HTTPS detection
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not CSRF_TRUSTED_ORIGINS or CSRF_TRUSTED_ORIGINS == [""]:
    # Fallback or empty if not provided
    CSRF_TRUSTED_ORIGINS = [ENV_SITE_URL.rstrip("/")]
if any(not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must use HTTPS in production")

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
