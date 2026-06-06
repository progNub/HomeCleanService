from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base.blocks import BaseStructBlock


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(required=True, label=_("Вопрос"))
    answer = blocks.RichTextBlock(required=True, label=_("Ответ"))

    class Meta:
        label = _("Вопрос-ответ")
        icon = "help"


class FAQBlock(BaseStructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок"), default=_("Часто задаваемые вопросы"))
    items = blocks.ListBlock(FAQItemBlock(), label=_("Список вопросов"))

    class Meta:
        label = _("Блок FAQ")
        template = "cms/home/blocks/faq.html"
        icon = "help"
