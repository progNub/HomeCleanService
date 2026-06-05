from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from cms.blocks.content import RichTextBlock
from cms.blocks.portfolio import (
    PortfolioComparisonBlock,
    PortfolioGalleryBlock,
    PortfolioImageBlock,
)
from cms.models.seo import SeoAbstract


class PortfolioIndexPage(SeoAbstract, Page):
    """
    Index page for Portfolio.
    """

    template = "cms/portfolio/portfolio_index_page.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.PortfolioWorkPage"]

    body = RichTextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Текст перед списком работ"),
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = SeoAbstract.promote_panels

    def get_context(self, request):
        context = super().get_context(request)
        context["works"] = PortfolioWorkPage.objects.child_of(self).live()
        return context

    class Meta:
        verbose_name = _("Наши работы")
        verbose_name_plural = _("Наши работы")


class PortfolioWorkPage(SeoAbstract, Page):
    template = "cms/portfolio/portfolio_work_page.html"
    parent_page_types = ["cms.PortfolioIndexPage"]

    main_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Основное изображение"),
    )
    short_description = models.TextField(blank=True, verbose_name=_("Краткое описание (для карточки)"))
    full_description = RichTextField(blank=True, verbose_name=_("Полное описание"))

    body = StreamField(
        [
            ("image", PortfolioImageBlock()),
            ("comparison", PortfolioComparisonBlock()),
            ("content", RichTextBlock()),
            ("gallery", PortfolioGalleryBlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
        verbose_name=_("Контент страницы"),
    )

    content_panels = Page.content_panels + [
        FieldPanel("main_image"),
        FieldPanel("short_description"),
        FieldPanel("full_description"),
        FieldPanel("body"),
    ]

    promote_panels = SeoAbstract.promote_panels

    def get_context(self, request):
        context = super().get_context(request)
        # Get 3 other live works from the same parent, excluding the current one
        context["other_works"] = (
            PortfolioWorkPage.objects.live().descendant_of(self.get_parent()).exclude(id=self.id).order_by("?")[:3]
        )
        return context

    class Meta:
        verbose_name = _("Работа")
        verbose_name_plural = _("Работы")
