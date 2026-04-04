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
            ('title', blocks.CharBlock(required=True, help_text=_("Banner title"))),
            ('subtitle', blocks.TextBlock(required=False, help_text=_("Subtitle"))),
            ('image', ImageChooserBlock(required=False, help_text=_("Background image"))),
            ('cta_text', blocks.CharBlock(
                required=False,
                label=_("Button text"),
                default=_("Order service")
            )),
        ], template='home/blocks/hero.html')),
        
        ('services', blocks.StructBlock([
            ('title', blocks.CharBlock(required=True, default=_("Our Services"))),
            ('items', blocks.ListBlock(blocks.StructBlock([
                ('name', blocks.CharBlock(required=True)),
                ('description', blocks.TextBlock(required=True)),
                ('image', ImageChooserBlock(required=False)),
            ]))),
        ], template='home/blocks/services.html')),
        
        ('content', blocks.RichTextBlock(label=_("Main content"), template='home/blocks/rich_text.html')),
    ], use_json_field=True, blank=True, null=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = _("Home Page")