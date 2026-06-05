from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cms.models.reviews import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["author", "text", "rating", "accept_privacy"]

        widgets = {
            "accept_privacy": forms.CheckboxInput(
                attrs={
                    "required": True,
                }
            ),
        }

    #
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_accept_privacy(self):
        data = self.cleaned_data.get("accept_privacy")
        if data is not True:
            raise ValidationError(_("Вы должны подтвердить согласие на обработку данных для отправки отзыва."))
        return data

    def clean(self):
        cleaned_data = super().clean()

        ip = self.request.META.get("REMOTE_ADDR")
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")

        # Проверка: один отзыв в 3 часа от одного пользователя (IP + UserAgent)
        cooldown_hours = 3
        cooldown_time = timezone.now() - timedelta(hours=cooldown_hours)

        last_review = (
            Review.objects.filter(ip=ip, user_agent=user_agent, date__gte=cooldown_time).order_by("-date").first()
        )
        if last_review:
            raise ValidationError(_("Вы можете оставлять отзывы только раз в 3 часа."))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.request:
            instance.ip = self.request.META.get("REMOTE_ADDR")
            instance.user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        if commit:
            instance.save()
        return instance
