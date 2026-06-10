import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField

from cms.models.seo import SeoAbstract
from cms.services.telegram.notifications import LeadNotificationService

from .builder import CUSTOM_FORM_FIELD_CHOICES, CustomFormBuilder

logger = logging.getLogger("notifications")


class FormField(AbstractFormField):
    page = ParentalKey("FormPage", on_delete=models.CASCADE, related_name="form_fields")

    class Meta:
        verbose_name = _("Поле формы")
        verbose_name_plural = _("Поля формы")
        ordering = ["sort_order"]

    field_type = models.CharField(verbose_name=_("field type"), max_length=32, choices=CUSTOM_FORM_FIELD_CHOICES)


class FormPage(SeoAbstract, AbstractEmailForm):
    form_builder = CustomFormBuilder

    intro = RichTextField(
        blank=True,
        verbose_name=_("Вступление"),
        help_text=_("Текст, который отображается перед полями формы"),
    )
    thank_you_text = RichTextField(
        blank=True,
        verbose_name=_("Текст после отправки"),
        help_text=_("Сообщение, которое увидит пользователь после успешной заполнения формы"),
    )

    def process_form_submission(self, form):
        """
        Overrides the default process_form_submission to save the data in the database
        but suppress the default email sending. This is a placeholder for future
        Telegram/SMS integration.
        """
        submission = self.get_submission_class().objects.create(
            form_data=form.cleaned_data,
            page=self,
        )

        try:
            notification_service = LeadNotificationService(submission)
            notification_service.send()
        except Exception:
            logger.exception(_("Error sending notification to Telegram"))

        # We return the submission object to allow Wagtail to show the success message,
        return submission

    class Meta:
        verbose_name = _("Страница с формой")
        verbose_name_plural = _("Страницы с формами")

    promote_panels = SeoAbstract.promote_panels

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
