from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable, PreviewableMixin

from .base import SettingsPreviewMixin


@register_setting
class NavigationSettings(SettingsPreviewMixin, PreviewableMixin, ClusterableModel, BaseGenericSetting):
    panels = [
        InlinePanel(
            "menu_items",
            label=_("Пункты меню"),
            help_text=_("Настройте ссылки в навигационной панели"),
        ),
    ]

    class Meta:
        verbose_name = _("Настройки навигации")


class MenuItem(Orderable):
    setting = ParentalKey(NavigationSettings, related_name="menu_items", on_delete=models.CASCADE)
    label = models.CharField(max_length=255, verbose_name=_("Заголовок"))
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Ссылка на страницу"),
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Внешняя ссылка или якорь"),
        help_text=_("Используйте для внешних ссылок или якорей (например, #services)"),
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_url:
            if self.link_url.startswith("#"):
                from cms.models import HomePage

                homepage = HomePage.objects.first()
                if homepage:
                    return f"{homepage.url}{self.link_url}"
            return self.link_url
        return "#"

    panels = [
        FieldPanel("label"),
        PageChooserPanel("link_page"),
        FieldPanel("link_url"),
    ]
