from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class ContactRequest(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Имя"))
    phone_validator = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message=_(
            "Номер телефона должен быть в формате: '+999999999'. Допускается до 15 цифр."
        ),
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=20,
        verbose_name=_("Номер телефона"),
        help_text=_("Укажите номер с кодом страны (например, +375...)"),
    )
    email = models.EmailField(
        blank=True, verbose_name=_("Email"), help_text=_("Ваш контактный email")
    )
    comment = models.TextField(blank=True, verbose_name=_("Комментарий"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата создания")
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("phone"),
                FieldPanel("email"),
                FieldPanel("comment"),
                FieldPanel("created_at", read_only=True),
            ],
            heading=_("Информация о заявке"),
        ),
    ]

    class Meta:
        verbose_name = _("Заявка на связь")
        verbose_name_plural = _("Заявки на связь")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.phone}"
