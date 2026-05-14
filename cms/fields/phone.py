from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class BYPhoneNumberField(models.CharField):
    default_validators = [
        RegexValidator(
            regex=r"^\+375\d{9}$",
            message=_(
                "Номер телефона должен быть в формате +375XXXXXXXXX (всего 13 символов)."
            ),
        )
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 13)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "error_messages": {
                "invalid": _("Введите корректный номер телефона."),
            }
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
