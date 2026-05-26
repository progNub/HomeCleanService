from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class BYPhoneFormField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "validators",
            [RegexValidator(r"^\+?375\d{9}$", message=_("Формат: 375XXXXXXXXX"))],
        )
        kwargs.setdefault("widget", forms.TextInput(attrs={"type": "tel"}))
        super().__init__(*args, **kwargs)
