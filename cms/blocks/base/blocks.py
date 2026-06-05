from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail import blocks


class BackgroundColorChoices(models.TextChoices):
    DEFAULT = "", _("По умолчанию (цвет страницы)")
    SECONDARY = "bg-body-secondary", _("Вторичный (минимальный контраст)")
    TERTIARY = "bg-body-tertiary", _("Третичный (легкий серый / графитовый)")


class PaddingVerticalChoices(models.TextChoices):
    PY_0 = "py-0", _("Без отступов")
    PY_1 = "py-1", _("Минимальный (1)")
    PY_2 = "py-2", _("Маленький (2)")
    PY_3 = "py-3", _("Средний (3)")
    PY_4 = "py-4", _("Большой (4)")
    PY_5 = "py-5", _("Максимальный (5)")


class BaseStructBlock(blocks.StructBlock):
    anchor = blocks.CharBlock(
        required=False,
        label=_("Якорь (ID)"),
        help_text=_("Уникальный идентификатор для перехода по ссылке (например, 'services')"),
    )
    background_color = blocks.ChoiceBlock(
        choices=BackgroundColorChoices.choices,
        required=False,
        default=BackgroundColorChoices.DEFAULT,
        label=_("Цвет фона"),
    )

    padding_vertical = blocks.ChoiceBlock(
        choices=PaddingVerticalChoices.choices,
        default=PaddingVerticalChoices.PY_5,
        label=_("Вертикальные отступы"),
        help_text=_("Управляет свободным пространством сверху и снизу блока"),
    )

    class Meta:
        abstract = True
