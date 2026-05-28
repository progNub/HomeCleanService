from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.utils.translation import gettext_lazy as _


class PortfolioImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Изображение"))
    caption = blocks.CharBlock(required=False, label=_("Подпись"))

    class Meta:
        icon = "image"
        label = _("Изображение")
        template = "cms/portfolio/blocks/image.html"


class PortfolioRichTextBlock(blocks.RichTextBlock):
    class Meta:
        icon = "doc-full"
        label = _("Текст")
        template = "cms/portfolio/blocks/rich_text.html"


class PortfolioComparisonBlock(blocks.StructBlock):
    image_before = ImageChooserBlock(label=_("Изображение ДО"))
    image_after = ImageChooserBlock(label=_("Изображение ПОСЛЕ"))
    caption = blocks.RichTextBlock(required=False, label=_("Описание"))

    class Meta:
        icon = "glitch"
        label = _("Сравнение (До/После)")
        template = "cms/portfolio/blocks/comparison.html"


class PortfolioGalleryBlock(blocks.StructBlock):
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
