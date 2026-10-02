"""Docker development worker: production dependencies, local service config."""

from .base import *

SECRET_KEY = ENV_DJANGO_SECRET_KEY or "django-insecure-local-worker-only"
DEBUG = False
SECURE_SSL_REDIRECT = False
WAGTAIL_CACHE = False
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
