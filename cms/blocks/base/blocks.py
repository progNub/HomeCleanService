from wagtail import blocks
from django.utils.translation import gettext_lazy as _


class BaseStructBlock(blocks.StructBlock):
    anchor = blocks.CharBlock(
        required=False,
        label=_("Якорь (ID)"),
        help_text=_(
            "Уникальный идентификатор для перехода по ссылке (например, 'services')"
        ),
    )

    class Meta:
        abstract = True
