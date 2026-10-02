from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from cms.forms import ReviewForm


@never_cache
@require_POST
def post_review(request):
    form = ReviewForm(request.POST, request=request)
    if form.is_valid():
        form.save(commit=True)
        request.session.pop("review_form_data", None)
        messages.success(request, _("Ваш отзыв отправлен на модерацию. Спасибо!"))
    else:
        # Only retain bounded, expected fields in the server-side session.
        # Preserve one extra character so max-length errors survive the redirect.
        limits = {"author": 256, "text": 2001, "rating": 10, "accept_privacy": 10}
        request.session["review_form_data"] = {
            field: request.POST.get(field, "")[:limit] for field, limit in limits.items()
        }
        messages.error(request, _("Пожалуйста, исправьте ошибки в форме отзыва."))

    redirect_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")
    if not url_has_allowed_host_and_scheme(
        redirect_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        redirect_url = "/"
    return redirect(redirect_url.split("#", 1)[0] + "#reviews")
