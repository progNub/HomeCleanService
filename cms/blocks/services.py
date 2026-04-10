from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.utils.translation import gettext_lazy as _
from .base.blocks import BaseStructBlock


class ServiceItemBlock(blocks.StructBlock):
    name = blocks.CharBlock(required=True, label=_("Название услуги"))
    description = blocks.TextBlock(required=True, label=_("Описание"))
    image = ImageChooserBlock(required=False, label=_("Изображение"))


class ServicesBlock(BaseStructBlock):
    title = blocks.CharBlock(
        required=True,
        label=_("Заголовок"),
        default=_("Наши услуги"),
    )
    items = blocks.ListBlock(ServiceItemBlock(), label=_("Список услуг"))

    class Meta:
        label = _("Блок услуг")
        template = "cms/home/blocks/services.html"
        icon = "list-ul"
