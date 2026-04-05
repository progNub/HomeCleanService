from django.db import models
from django.utils.translation import gettext_lazy as _ # Импорт для переводов

from wagtail.models import Page, TranslatableMixin

from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.images.blocks import ImageChooserBlock

class HomePage(Page, TranslatableMixin):
    body = StreamField([
        ('hero', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"), help_text=_("Заголовок баннера"))),
            ('subtitle', blocks.TextBlock(required=False, label=_("Подзаголовок"), help_text=_("Подзаголовок"))),
            ('image', ImageChooserBlock(required=False, label=_("Изображение"), help_text=_("Фоновое изображение"))),
            ('cta_text', blocks.CharBlock(
                required=False,
                label=_("Текст кнопки"),
                default=_("Рассчитать стоимость")
            )),
        ], label=_("Главный баннер"), template='home/blocks/hero.html')),
        
        ('services', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"), default=_("Наши услуги"))),
            ('items', blocks.ListBlock(blocks.StructBlock([
                ('name', blocks.CharBlock(required=True, label=_("Название услуги"))),
                ('description', blocks.TextBlock(required=True, label=_("Описание"))),
                ('image', ImageChooserBlock(required=False, label=_("Изображение"))),
            ]), label=_("Список услуг"))),
        ], label=_("Блок услуг"), template='home/blocks/services.html')),

        ('features', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"))),
            ('items', blocks.ListBlock(blocks.StructBlock([
                ('title', blocks.CharBlock(required=True, label=_("Заголовок преимущества"))),
                ('text', blocks.TextBlock(required=True, label=_("Текст преимущества"))),
            ]), label=_("Преимущества"))),
        ], label=_("Преимущества"), template='home/blocks/features.html')),

        ('contact_form', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок формы"), default=_("Оставьте заявку"))),
            ('subtitle', blocks.TextBlock(required=False, label=_("Подзаголовок формы"), default=_("Мы свяжемся с вами для уточнения деталей"))),
        ], label=_("Форма обратной связи"), template='home/blocks/contact_form.html')),
        
        ('content', blocks.RichTextBlock(label=_("Основной текст"), template='home/blocks/rich_text.html')),
    ], use_json_field=True, blank=True, null=True, verbose_name=_("Контент страницы"))

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = _("Главная страница")