from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from cms.forms import ReviewForm
from cms.models import Review


def post_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Получаем данные пользователя
            ip = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")

            # Проверка: один отзыв в 3 часа от одного пользователя (IP + UserAgent)
            cooldown_hours = 3
            cooldown_time = timezone.now() - timedelta(hours=cooldown_hours)

            last_review = (
                Review.objects.filter(
                    ip=ip, user_agent=user_agent, date__gte=cooldown_time
                )
                .order_by("-date")
                .first()
            )

            if last_review:
                # Расчет оставшегося времени
                time_passed = timezone.now() - last_review.date
                remaining_time = timedelta(hours=cooldown_hours) - time_passed

                hours_left = int(remaining_time.total_seconds() // 3600)
                minutes_left = int((remaining_time.total_seconds() % 3600) // 60)

                time_str = ""
                if hours_left > 0:
                    time_str += f"{hours_left} ч. "
                time_str += f"{minutes_left} мин."

                messages.error(
                    request,
                    _(
                        "Вы можете оставлять отзывы только раз в 3 часа. Пожалуйста, подождите еще {time_str}."
                    ).format(time_str=time_str),
                )
            else:
                review = form.save(commit=False)
                # Отзыв по умолчанию не одобрен (модерация)
                review.is_approved = False
                review.ip = ip
                review.user_agent = user_agent
                review.save()
                messages.success(
                    request, _("Ваш отзыв отправлен на модерацию. Спасибо!")
                )
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
