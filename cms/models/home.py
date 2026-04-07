from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.images.blocks import ImageChooserBlock

from contacts.forms import ContactForm


class HomePage(Page):
    template = 'cms/home/home_page.html'

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
        ], label=_("Главный баннер"), template='cms/home/blocks/hero.html')),

        ('services', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"), default=_("Наши услуги"))),
            ('items', blocks.ListBlock(blocks.StructBlock([
                ('name', blocks.CharBlock(required=True, label=_("Название услуги"))),
                ('description', blocks.TextBlock(required=True, label=_("Описание"))),
                ('image', ImageChooserBlock(required=False, label=_("Изображение"))),
            ]), label=_("Список услуг"))),
        ], label=_("Блок услуг"), template='cms/home/blocks/services.html')),

        ('features', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"))),
            ('items', blocks.ListBlock(blocks.StructBlock([
                ('title', blocks.CharBlock(required=True, label=_("Заголовок преимущества"))),
                ('text', blocks.TextBlock(required=True, label=_("Текст преимущества"))),
            ]), label=_("Преимущества"))),
        ], label=_("Преимущества"), template='cms/home/blocks/features.html')),

        ('contact_form', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок формы"), default=_("Оставьте заявку"))),
            ('subtitle', blocks.TextBlock(required=False, label=_("Подзаголовок формы"),
                                          default=_("Мы свяжемся с вами для уточнения деталей"))),
        ], label=_("Форма обратной связи"), template='cms/home/blocks/contact_form.html')),

        ('about', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, label=_("Заголовок"))),
            ('content', blocks.RichTextBlock(required=True, label=_("Содержимое"))),
            ('image', ImageChooserBlock(required=False, label=_("Изображение"))),
            ('stats', blocks.ListBlock(blocks.StructBlock([
                ('value', blocks.CharBlock(required=True, label=_("Значение (напр. 10+)"))),
                ('label', blocks.CharBlock(required=True, label=_("Подпись (напр. лет опыта)"))),
            ]), label=_("Показатели/Статистика"), required=False)),
        ], label=_("О нас"), template='cms/home/blocks/about.html')),

        ('content', blocks.RichTextBlock(label=_("Основной текст"), template='cms/home/blocks/rich_text.html')),
    ], use_json_field=True, blank=True, null=True, verbose_name=_("Контент страницы"))

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = _("Главная страница")

    def serve(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        form_success = None
        form_message = None

        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                # Проверяем, не является ли заявка дубликатом (установлено в clean_phone)
                is_duplicate = getattr(form, 'is_duplicate', False)

                if not is_duplicate:
                    form.save()
                
                form_success = True
                form_message = _("Заявка успешно принята!")
                # Очищаем форму после успеха
                form = ContactForm()
            else:
                form_success = False
                form_message = _("Исправьте ошибки в форме.")
        else:
            form = ContactForm()

        # Передаем всё в контекст
        context.update({
            "contact_form": form,
            "form_success": form_success,
            "form_message": form_message
        })

        return TemplateResponse(request, self.get_template(request, *args, **kwargs), context)
