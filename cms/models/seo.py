from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class SeoAbstract(models.Model):
    """
    Abstract base class that adds comprehensive SEO fields to pages.
    Includes OG tags, Twitter cards, meta robots, and other SEO enhancements.
    """

    class MetaRobotsChoices(models.TextChoices):
        INDEX_FOLLOW = (
            "index, follow",
            _("Индексировать, переходить по ссылкам (Index, Follow)"),
        )
        NOINDEX_FOLLOW = (
            "noindex, follow",
            _("Не индексировать, переходить по ссылкам (Noindex, Follow)"),
        )
        INDEX_NOFOLLOW = (
            "index, nofollow",
            _("Индексировать, не переходить по ссылкам (Index, Nofollow)"),
        )
        NOINDEX_NOFOLLOW = (
            "noindex, nofollow",
            _("Не индексировать, не переходить по ссылкам (Noindex, Nofollow)"),
        )

    class OgTypeChoices(models.TextChoices):
        WEBSITE = "website", _("Веб-сайт (Website)")
        ARTICLE = "article", _("Статья (Article)")
        PRODUCT = "product", _("Товар (Product)")
        PROFILE = "profile", _("Профиль (Profile)")
        VIDEO = "video.other", _("Видео (Video)")

    # SEO Image fields
    og_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Изображение Open Graph"),
        help_text=_(
            "Загрузите кастомное изображение OG для соцсетей. Рекомендуемый размер: 1200x630px. Если не указано, будет использовано изображение родительской страницы или логотип сайта."
        ),
        related_name="+",
    )

    # Meta robots
    meta_robots = models.CharField(
        max_length=20,
        choices=MetaRobotsChoices,
        null=True,
        blank=True,
        verbose_name=_("Тег Robots"),
        help_text=_("Управление тем, как поисковые системы индексируют эту страницу"),
    )

    # Additional OG fields
    og_type = models.CharField(
        max_length=20,
        choices=OgTypeChoices,
        default=OgTypeChoices.WEBSITE,
        verbose_name=_("Тип Open Graph"),
        help_text=_("Тип объекта в Open Graph (website, article и т.д.)"),
    )

    canonical_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Канонический URL"),
        help_text=_(
            "Если оставить пустым, будет использован текущий URL страницы. Используйте, если контент дублируется на другой странице."
        ),
    )

    published_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Дата публикации"),
        help_text=_(
            "Дата и время публикации страницы для поисковых систем (Open Graph)"
        ),
    )

    modified_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Дата изменения"),
        help_text=_(
            "Дата и время последнего изменения страницы для поисковых систем (Open Graph). Если не указано, будет использовано системное время изменения."
        ),
    )

    promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug"),
            ],
            heading=_("URL-адрес страницы (Slug)"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("seo_title", heading=_("Заголовок страницы (Title)")),
                FieldPanel(
                    "search_description", heading=_("Мета-описание (Description)")
                ),
                FieldPanel("og_image"),
                FieldPanel("og_type"),
                FieldPanel("meta_robots"),
                FieldPanel("canonical_url"),
                FieldPanel("published_date"),
                FieldPanel("modified_date"),
            ],
            heading=_("SEO и Социальные сети"),
            help_text=_(
                "Настройте параметры SEO и отображения страницы в социальных сетях."
            ),
        ),
    ]

    def get_og_image_url(self, request=None):
        """
        Get the OG image URL with fallback logic.
        Returns absolute URL if request is provided, relative URL otherwise.
        """

        def get_compressed_image(image):
            return image.get_rendition("fill-1200x630|format-webp").url

        relative_url = ""

        if self.og_image:
            relative_url = get_compressed_image(self.og_image)
        else:
            parent_page = self.get_parent()
            # Пытаемся получить специфическую версию страницы, если это возможно
            try:
                site = self.get_site()
                root_page = site.root_page.specific if site else None
            except Exception:
                root_page = None

            if (
                parent_page
                and hasattr(parent_page.specific, "og_image")
                and parent_page.specific.og_image
            ):
                relative_url = get_compressed_image(parent_page.specific.og_image)
            elif root_page and hasattr(root_page, "logo") and root_page.logo:
                relative_url = get_compressed_image(root_page.logo)
            elif hasattr(self, "logo") and self.logo:
                relative_url = get_compressed_image(self.logo)

        if relative_url and request:
            return request.build_absolute_uri(relative_url)
        return relative_url

    @property
    def og_image_url(self):
        """
        Get the OG image URL with fallback logic (relative URL).
        For absolute URLs, use get_og_image_url(request) method.
        """
        return self.get_og_image_url()

    def get_context(self, request, *args, **kwargs):
        """
        Add request to context for SEO template tags.
        """
        context = super().get_context(request, *args, **kwargs)
        context["request"] = request
        return context

    class Meta:
        abstract = True
