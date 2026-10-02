"""Asset collection only: deterministic and independent of production secrets/DB."""

from .base import *

SECRET_KEY = "build-only-not-used-at-runtime"
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATIC_ROOT = os.getenv("BUILD_STATIC_ROOT", "/opt/homeservice/static")
TELEGRAM_BOT_TOKEN = None
TELEGRAM_LOGS_CHAT_ID = None
TELEGRAM_NOTIFICATIONS_CHAT_ID = None
LOGGING = {"version": 1, "disable_existing_loggers": False}
