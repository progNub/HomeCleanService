from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import PreviewableMixin

from .base import SettingsPreviewMixin


@register_setting
class ContactSettings(SettingsPreviewMixin, PreviewableMixin, BaseGenericSetting):
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Номер телефона"),
        help_text=_("Основной номер телефона"),
    )
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"), help_text=_("Контактный email"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Адрес"), help_text=_("Адрес офиса"))
    legal_full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Юридическое ФИО"),
        help_text=_("Полное ФИО индивидуального предпринимателя"),
    )
    legal_unp = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("УНП"),
        help_text=_("Учетный номер плательщика"),
    )
    legal_address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Юридический адрес"),
        help_text=_("Адрес регистрации"),
    )
    legal_reg_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Дата регистрации"),
        help_text=_("Дата государственной регистрации"),
    )
    privacy_policy_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Страница политики конфиденциальности"),
    )
    terms_of_service_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Страница пользовательского соглашения"),
    )
    legal_index_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Главная юридическая страница"),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("phone_number"),
                FieldPanel("email"),
                FieldPanel("address"),
            ],
            heading=_("Контактная информация"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("legal_full_name"),
                FieldPanel("legal_unp"),
                FieldPanel("legal_address"),
                FieldPanel("legal_reg_date"),
            ],
            heading=_("Юридическая информация"),
        ),
        MultiFieldPanel(
            [
                PageChooserPanel("legal_index_page", "cms.LegalIndexPage"),
                PageChooserPanel("privacy_policy_page", "cms.LegalDocumentPage"),
                PageChooserPanel("terms_of_service_page", "cms.LegalDocumentPage"),
            ],
            heading=_("Юридические документы"),
        ),
    ]

    class Meta:
        verbose_name = _("Контактные данные")
