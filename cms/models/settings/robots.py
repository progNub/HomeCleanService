from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable


@register_setting
class RobotsSettings(ClusterableModel, BaseGenericSetting):
    panels = [
        InlinePanel(
            "disallow_rules",
            label=_("Запрещённые пути"),
            help_text=_("Пути, которые поисковые роботы не должны индексировать"),
        ),
    ]

    class Meta:
        verbose_name = _("Настройки robots.txt")


class RobotsDisallowRule(Orderable):
    setting = ParentalKey(RobotsSettings, related_name="disallow_rules", on_delete=models.CASCADE)
    path = models.CharField(
        max_length=500,
        verbose_name=_("Путь"),
        help_text=_("Например: /admin/ или /private/"),
    )

    panels = [FieldPanel("path")]

    class Meta(Orderable.Meta):
        verbose_name = _("Запрещённый путь")
        verbose_name_plural = _("Запрещённые пути")
