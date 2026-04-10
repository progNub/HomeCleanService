from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.utils.translation import gettext_lazy as _
from .base.blocks import BaseStructBlock


class HeroBlock(BaseStructBlock):
    title = blocks.CharBlock(
        required=True,
        label=_("Заголовок"),
        help_text=_("Заголовок баннера"),
    )
    subtitle = blocks.TextBlock(
        required=False,
        label=_("Подзаголовок"),
        help_text=_("Подзаголовок"),
    )
    image = ImageChooserBlock(
        required=False,
        label=_("Изображение"),
        help_text=_("Фоновое изображение"),
    )
    cta_text = blocks.CharBlock(
        required=False,
        label=_("Текст кнопки"),
        default=_("Рассчитать стоимость"),
    )
    cta_page = blocks.PageChooserBlock(
        required=False,
        label=_("Целевая страница"),
        help_text=_("Выберите страницу, на которую ведет кнопка"),
    )

    class Meta:
        label = _("Главный баннер")
        template = "cms/home/blocks/hero.html"
        icon = "image"
