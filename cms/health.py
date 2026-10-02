from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@never_cache
@require_safe
def health(request):
    return JsonResponse({"status": "ok", "revision": settings.RELEASE_REVISION})


@never_cache
@require_safe
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.get("homeservice-readiness")
    except Exception:
        # Never publish database/cache connection details or credentials.
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "revision": settings.RELEASE_REVISION})
