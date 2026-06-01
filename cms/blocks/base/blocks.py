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
    background_color = blocks.ChoiceBlock(
        choices=[
            ("", _("По умолчанию (цвет страницы)")),
            ("bg-body-secondary", _("Вторичный (минимальный контраст)")),
            ("bg-body-tertiary", _("Третичный (легкий серый / графитовый)")),
        ],
        required=False,
        default="",
        label=_("Цвет фона"),
    )
    padding_vertical = blocks.ChoiceBlock(
        choices=[
            ("py-0", _("Без отступов")),
            ("py-1", _("Минимальный (1)")),
            ("py-2", _("Маленький (2)")),
            ("py-3", _("Средний (3)")),
            ("py-4", _("Большой (4)")),
            ("py-5", _("Максимальный (5)")),
        ],
        default="py-5",
        label=_("Вертикальные отступы"),
        help_text=_("Управляет свободным пространством сверху и снизу блока"),
    )

    class Meta:
        abstract = True
