from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable, PreviewableMixin

from .base import SettingsPreviewMixin


@register_setting
class SocialMediaSettings(
    SettingsPreviewMixin, PreviewableMixin, ClusterableModel, BaseGenericSetting
):
    panels = [
        InlinePanel(
            "social_media_links",
            label=_("Ссылки на соцсети"),
            help_text=_("Добавьте ссылки на ваши профили в социальных сетях"),
        )
    ]

    class Meta:
        verbose_name = _("Настройки соцсетей")


class SocialMediaLink(Orderable):
    PLATFORM_CHOICES = [
        ("facebook", "Facebook"),
        ("instagram", "Instagram"),
        ("youtube", "YouTube"),
        ("telegram", "Telegram"),
        ("whatsapp", "WhatsApp"),
        ("vk", "VK"),
        ("viber", "Viber"),
        ("tiktok", "TikTok"),
    ]

    setting = ParentalKey(
        SocialMediaSettings, related_name="social_media_links", on_delete=models.CASCADE
    )
    platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, verbose_name=_("Платформа")
    )
    url = models.URLField(verbose_name=_("Ссылка"))

    panels = [
        FieldPanel("platform"),
        FieldPanel("url"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = _("Ссылка на соцсеть")
        verbose_name_plural = _("Ссылки на соцсети")
