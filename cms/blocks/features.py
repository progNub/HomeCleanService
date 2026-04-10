from wagtail import blocks
from django.utils.translation import gettext_lazy as _
from .base.blocks import BaseStructBlock


class FeatureItemBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок преимущества"))
    text = blocks.TextBlock(required=True, label=_("Текст преимущества"))


class FeaturesBlock(BaseStructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок"))
    items = blocks.ListBlock(FeatureItemBlock(), label=_("Преимущества"))

    class Meta:
        label = _("Преимущества")
        template = "cms/home/blocks/features.html"
        icon = "tick-inverse"
