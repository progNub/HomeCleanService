from wagtail import blocks
from django.utils.translation import gettext_lazy as _

from .base.blocks import BaseStructBlock


class RichTextBlock(BaseStructBlock):
    content = blocks.RichTextBlock(label=_("Содержимое"))

    class Meta:
        label = _("Основной текст")
        template = "cms/home/blocks/rich_text.html"
        icon = "doc-full"
