from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable, PreviewableMixin

from .base import SettingsPreviewMixin


@register_setting
class ScriptSettings(SettingsPreviewMixin, PreviewableMixin, ClusterableModel, BaseSiteSetting):
    """
    Settings for external scripts (Analytics, Chat widgets, etc.)
    """

    select_related = ("site",)

    site = models.ForeignKey(
        "wagtailcore.Site",
        on_delete=models.CASCADE,
        editable=False,
        related_name="+",
        default=2,
    )

    panels = [
        InlinePanel(
            "custom_scripts",
            label=_("Пользовательские скрипты"),
            help_text=_("Добавьте дополнительные коды отслеживания (Google Analytics, Яндекс.Метрика и др.)"),
        ),
    ]

    class Meta:
        verbose_name = _("Настройки скриптов")


class LocationChoices(models.TextChoices):
    HEAD = ("head", _("Внутри <head>"))
    BODY_TOP = ("body_top", _("После начала <body>"))
    BODY_BOTTOM = ("body_bottom", _("Перед концом </body>"))


class ScriptSnippet(Orderable):
    setting = ParentalKey(ScriptSettings, related_name="custom_scripts", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name=_("Название скрипта"))
    code = models.TextField(verbose_name=_("Код скрипта"))
    location = models.CharField(
        max_length=20,
        choices=LocationChoices,
        default="head",
        verbose_name=_("Место размещения"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))

    panels = [
        FieldPanel("name"),
        FieldPanel("code"),
        FieldPanel("location"),
        FieldPanel("is_active"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = _("Пользовательский скрипт")
        verbose_name_plural = _("Пользовательские скрипты")
