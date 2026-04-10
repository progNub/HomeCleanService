from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock
from django.utils.translation import gettext_lazy as _
from .base.blocks import BaseStructBlock


class ReviewsBlock(BaseStructBlock):
    title = blocks.CharBlock(
        required=True, label=_("Заголовок"), default=_("Отзывы наших клиентов")
    )
    reviews = blocks.ListBlock(
        SnippetChooserBlock("cms.Review"),
        label=_("Отзывы"),
        help_text=_("Выберите отзывы для отображения"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        from cms.forms import ReviewForm

        context["review_form"] = ReviewForm()
        return context

    class Meta:
        label = _("Блок отзывов")
        template = "cms/home/blocks/reviews.html"
        icon = "comment"
