from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
    PageChooserPanel,
)
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable, PreviewableMixin


@register_setting
class SocialMediaSettings(PreviewableMixin, BaseGenericSetting):
    facebook = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Facebook"),
        help_text=_("Ссылка на Facebook"),
    )
    instagram = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Instagram"),
        help_text=_("Ссылка на Instagram"),
    )
    youtube = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("YouTube"),
        help_text=_("Ссылка на YouTube"),
    )
    telegram = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Telegram"),
        help_text=_("Ссылка на Telegram"),
    )
    whatsapp = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("WhatsApp"),
        help_text=_("Ссылка на WhatsApp"),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("facebook"),
                FieldPanel("instagram"),
                FieldPanel("youtube"),
                FieldPanel("telegram"),
                FieldPanel("whatsapp"),
            ],
            heading=_("Социальные сети"),
        )
    ]

    class Meta:
        verbose_name = _("Настройки соцсетей")

    def get_preview_template(self, request, mode_name):
        return "cms/home/home_page.html"

    def get_preview_context(self, request, mode_name):
        from cms.models import HomePage

        homepage = HomePage.objects.first()
        context = homepage.get_context(request)
        if "settings" not in context:
            context["settings"] = {}
        if "cms" not in context["settings"]:
            context["settings"]["cms"] = {}
        context["settings"]["cms"]["SocialMediaSettings"] = self
        return context


@register_setting
class ContactSettings(PreviewableMixin, BaseGenericSetting):
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Номер телефона"),
        help_text=_("Основной номер телефона"),
    )
    email = models.EmailField(
        blank=True, null=True, verbose_name=_("Email"), help_text=_("Контактный email")
    )
    address = models.TextField(
        blank=True, null=True, verbose_name=_("Адрес"), help_text=_("Адрес офиса")
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("phone_number"),
                FieldPanel("email"),
                FieldPanel("address"),
            ],
            heading=_("Контактная информация"),
        )
    ]

    class Meta:
        verbose_name = _("Контактные данные")

    def get_preview_template(self, request, mode_name):
        return "cms/home/home_page.html"

    def get_preview_context(self, request, mode_name):
        from cms.models import HomePage

        homepage = HomePage.objects.first()
        context = homepage.get_context(request)
        if "settings" not in context:
            context["settings"] = {}
        if "cms" not in context["settings"]:
            context["settings"]["cms"] = {}
        context["settings"]["cms"]["ContactSettings"] = self
        return context


@register_setting
class NavigationSettings(PreviewableMixin, ClusterableModel, BaseGenericSetting):
    panels = [
        InlinePanel(
            "menu_items",
            label=_("Пункты меню"),
            help_text=_("Настройте ссылки в навигационной панели"),
        ),
    ]

    class Meta:
        verbose_name = _("Настройки навигации")

    def get_preview_template(self, request, mode_name):
        return "cms/home/home_page.html"

    def get_preview_context(self, request, mode_name):
        from cms.models import HomePage

        homepage = HomePage.objects.first()
        context = homepage.get_context(request)
        # Мы заменяем настройки в контексте на текущие (несохраненные)
        # В шаблоне header.html используется {% get_settings %} и settings.cms.NavigationSettings
        # Wagtail settings обычно доступны через settings.app_label.ModelName
        if "settings" not in context:
            context["settings"] = {}
        if "cms" not in context["settings"]:
            context["settings"]["cms"] = {}
        context["settings"]["cms"]["NavigationSettings"] = self
        return context


class MenuItem(Orderable):
    setting = ParentalKey(
        NavigationSettings, related_name="menu_items", on_delete=models.CASCADE
    )
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
            return self.link_url
        return "#"

    panels = [
        FieldPanel("label"),
        PageChooserPanel("link_page"),
        FieldPanel("link_url"),
    ]
