from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting

@register_setting
class SocialMediaSettings(BaseGenericSetting):
    facebook = models.URLField(blank=True, null=True, help_text=_("Facebook URL"))
    instagram = models.URLField(blank=True, null=True, help_text=_("Instagram URL"))
    youtube = models.URLField(blank=True, null=True, help_text=_("YouTube URL"))
    telegram = models.URLField(blank=True, null=True, help_text=_("Telegram URL"))
    whatsapp = models.URLField(blank=True, null=True, help_text=_("WhatsApp URL"))

    panels = [
        MultiFieldPanel([
            FieldPanel("facebook"),
            FieldPanel("instagram"),
            FieldPanel("youtube"),
            FieldPanel("telegram"),
            FieldPanel("whatsapp"),
        ], heading=_("Social Media"))
    ]

    class Meta:
        verbose_name = _("Social Media")


@register_setting
class ContactSettings(BaseGenericSetting):
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text=_("Primary phone number"))
    email = models.EmailField(blank=True, null=True, help_text=_("Contact email"))
    address = models.TextField(blank=True, null=True, help_text=_("Office address"))

    panels = [
        MultiFieldPanel([
            FieldPanel("phone_number"),
            FieldPanel("email"),
            FieldPanel("address"),
        ], heading=_("Contact Information"))
    ]

    class Meta:
        verbose_name = _("Contact Details")
