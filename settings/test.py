"""Isolated tests: never load the developer's .env or contact providers."""

from .base import *

SECRET_KEY = "test-only-secret-0123456789-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
WAGTAILADMIN_BASE_URL = "http://testserver"
if os.getenv("TEST_POSTGRES") != "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
WAGTAIL_CACHE = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
TELEGRAM_BOT_TOKEN = None
TELEGRAM_LOGS_CHAT_ID = None
TELEGRAM_NOTIFICATIONS_CHAT_ID = None
TASKS = {"default": {"BACKEND": "django.tasks.backends.dummy.DummyBackend", "QUEUES": ["default", "notifications"]}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}
MEDIA_ROOT = os.getenv("TEST_MEDIA_ROOT", "/tmp/homeservice-test-media")
STATIC_ROOT = os.getenv("TEST_STATIC_ROOT", "/tmp/homeservice-test-static")
