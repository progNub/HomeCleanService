from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting

@register_setting
class SocialMediaSettings(BaseGenericSetting):
    facebook = models.URLField(blank=True, null=True, verbose_name=_("Facebook"), help_text=_("Ссылка на Facebook"))
    instagram = models.URLField(blank=True, null=True, verbose_name=_("Instagram"), help_text=_("Ссылка на Instagram"))
    youtube = models.URLField(blank=True, null=True, verbose_name=_("YouTube"), help_text=_("Ссылка на YouTube"))
    telegram = models.URLField(blank=True, null=True, verbose_name=_("Telegram"), help_text=_("Ссылка на Telegram"))
    whatsapp = models.URLField(blank=True, null=True, verbose_name=_("WhatsApp"), help_text=_("Ссылка на WhatsApp"))

    panels = [
        MultiFieldPanel([
            FieldPanel("facebook"),
            FieldPanel("instagram"),
            FieldPanel("youtube"),
            FieldPanel("telegram"),
            FieldPanel("whatsapp"),
        ], heading=_("Социальные сети"))
    ]

    class Meta:
        verbose_name = _("Настройки соцсетей")


@register_setting
class ContactSettings(BaseGenericSetting):
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Номер телефона"), help_text=_("Основной номер телефона"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"), help_text=_("Контактный email"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Адрес"), help_text=_("Адрес офиса"))

    panels = [
        MultiFieldPanel([
            FieldPanel("phone_number"),
            FieldPanel("email"),
            FieldPanel("address"),
        ], heading=_("Контактная информация"))
    ]

    class Meta:
        verbose_name = _("Контактные данные")
