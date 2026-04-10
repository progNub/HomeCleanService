from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


class FormField(AbstractFormField):
    page = ParentalKey("FormPage", on_delete=models.CASCADE, related_name="form_fields")

    class Meta:
        verbose_name = _("Поле формы")
        verbose_name_plural = _("Поля формы")


class FormPage(AbstractEmailForm):
    intro = RichTextField(
        blank=True,
        verbose_name=_("Вступление"),
        help_text=_("Текст, который отображается перед полями формы"),
    )
    thank_you_text = RichTextField(
        blank=True,
        verbose_name=_("Текст после отправки"),
        help_text=_(
            "Сообщение, которое увидит пользователь после успешной заполнения формы"
        ),
    )

    class Meta:
        verbose_name = _("Страница с формой")
        verbose_name_plural = _("Страницы с формами")

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel(
            "form_fields",
            label=_("Конструктор полей"),
            help_text=_("Добавьте поля, которые должен заполнить пользователь"),
        ),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address"),
                        FieldPanel("to_address"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            _("Настройки уведомлений (Email)"),
        ),
    ]
