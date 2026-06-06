from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from .base.blocks import BaseStructBlock


class StatBlock(blocks.StructBlock):
    value = blocks.CharBlock(required=True, label=_("Значение (напр. 10+)"))
    label = blocks.CharBlock(required=True, label=_("Подпись (напр. лет опыта)"))


class AboutBlock(BaseStructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок"))
    content = blocks.RichTextBlock(required=True, label=_("Содержимое"))
    image = ImageChooserBlock(required=False, label=_("Изображение"))
    stats = blocks.ListBlock(StatBlock(), label=_("Показатели/Статистика"), required=False)

    class Meta:
        label = _("О нас")
        template = "cms/home/blocks/about.html"
        icon = "info-circle"
