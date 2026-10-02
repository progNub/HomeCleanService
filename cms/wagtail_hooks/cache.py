from django.conf import settings
from wagtail import hooks


@hooks.register("is_request_cacheable")
def skip_personal_feedback(request, is_cacheable):
    # Skip before lookup as well as after render: a cached page would otherwise
    # hide validation errors, and a cache write could expose a submitted review.
    if settings.SESSION_COOKIE_NAME in request.COOKIES or "messages" in request.COOKIES:
        return False
    if hasattr(request, "session") and request.session.get("review_form_data") is not None:
        return False
    return is_cacheable
