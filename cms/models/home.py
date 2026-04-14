from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel

from cms.models.seo import SeoAbstract
from cms.blocks.hero import HeroBlock
from cms.blocks.services import ServicesBlock
from cms.blocks.features import FeaturesBlock
from cms.blocks.about import AboutBlock
from cms.blocks.reviews import ReviewsBlock
from cms.blocks.faq import FAQBlock
from cms.blocks.content import RichTextBlock


class HomePage(SeoAbstract, Page):
    template = "cms/home/home_page.html"

    body = StreamField(
        [
            ("hero", HeroBlock()),
            ("services", ServicesBlock()),
            ("features", FeaturesBlock()),
            ("about", AboutBlock()),
            ("reviews", ReviewsBlock()),
            ("faq", FAQBlock()),
            ("content", RichTextBlock()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
        verbose_name=_("Контент страницы"),
    )

    promote_panels = SeoAbstract.promote_panels

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = _("Главная страница")
