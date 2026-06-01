from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.utils.translation import gettext_lazy as _
from cms.blocks.base import BaseStructBlock


class PortfolioImageBlock(BaseStructBlock):
    image = ImageChooserBlock(label=_("Изображение"))
    caption = blocks.CharBlock(required=False, label=_("Подпись"))

    class Meta:
        icon = "image"
        label = _("Изображение")
        template = "cms/portfolio/blocks/image.html"


class PortfolioComparisonBlock(BaseStructBlock):
    image_before = ImageChooserBlock(label=_("Изображение ДО"))
    image_after = ImageChooserBlock(label=_("Изображение ПОСЛЕ"))
    caption = blocks.RichTextBlock(required=False, label=_("Описание"))

    class Meta:
        icon = "glitch"
        label = _("Сравнение (До/После)")
        template = "cms/portfolio/blocks/comparison.html"


class PortfolioGalleryBlock(BaseStructBlock):
    images = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("image", ImageChooserBlock(label=_("Изображение"))),
                ("caption", blocks.CharBlock(required=False, label=_("Подпись"))),
            ]
        ),
        label=_("Галерея"),
    )

    class Meta:
        icon = "image"
        label = _("Сетка изображений")
        template = "cms/portfolio/blocks/gallery.html"
