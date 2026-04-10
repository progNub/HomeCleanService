from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from cms.forms import ReviewForm


def post_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            # Отзыв по умолчанию не одобрен (модерация)
            review.is_approved = False
            review.save()
            messages.success(request, _("Ваш отзыв отправлен на модерацию. Спасибо!"))
        else:
            messages.error(
                request,
                _(
                    "Произошла ошибка при отправке отзыва. Пожалуйста, проверьте данные."
                ),
            )

    redirect_url = request.META.get("HTTP_REFERER", "/")
    # Простейшая очистка от старых якорей и добавление нужного
    if "#" in redirect_url:
        redirect_url = redirect_url.split("#")[0]

    redirect_url += "#reviews"

    return redirect(redirect_url)
