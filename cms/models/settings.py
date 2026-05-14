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


class SettingsPreviewMixin:
    """
    Mixin to provide common preview logic for settings models.
    It injects the current (unsaved) settings instance into the context
    under the key used by Wagtail's {% get_settings %} tag.
    """

    def get_preview_template(self, request, mode_name):
        return "cms/home/home_page.html"

    def get_preview_context(self, request, mode_name):
        from cms.models import HomePage

        homepage = HomePage.objects.first()
        context = homepage.get_context(request) if homepage else {"request": request}

        # Wagtail settings are usually accessed in templates as
        # {{ settings.app_label.ModelName }} after {% get_settings %}
        if "settings" not in context:
            context["settings"] = {}
        if "cms" not in context["settings"]:
            context["settings"]["cms"] = {}

        # self is the current instance being previewed (including unsaved changes)
        context["settings"]["cms"][self.__class__.__name__] = self
        return context


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


@register_setting
class ContactSettings(SettingsPreviewMixin, PreviewableMixin, BaseGenericSetting):
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
    setting = ParentalKey(
        RobotsSettings, related_name="disallow_rules", on_delete=models.CASCADE
    )
    path = models.CharField(
        max_length=500,
        verbose_name=_("Путь"),
        help_text=_("Например: /admin/ или /private/"),
    )

    panels = [FieldPanel("path")]

    class Meta(Orderable.Meta):
        verbose_name = _("Запрещённый путь")
        verbose_name_plural = _("Запрещённые пути")


@register_setting
class NavigationSettings(
    SettingsPreviewMixin, PreviewableMixin, ClusterableModel, BaseGenericSetting
):
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
