from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from cms.forms import ReviewForm


def _get_prepared_form_errors(form):
    if not form.errors:
        return ""
    return " ".join([error for errors in form.errors.values() for error in errors])


def post_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST, request=request)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, _("Ваш отзыв отправлен на модерацию. Спасибо!"))
        else:
            form_errors = _get_prepared_form_errors(form)
            text_error = form_errors or _("Произошла ошибка при отправке отзыва. Пожалуйста, проверьте данные.")
            messages.error(request, text_error)

    redirect_url = request.META.get("HTTP_REFERER", "/")
    # Простейшая очистка от старых якорей и добавление нужного
    if "#" in redirect_url:
        redirect_url = redirect_url.split("#")[0]

    redirect_url += "#reviews"

    return redirect(redirect_url)
