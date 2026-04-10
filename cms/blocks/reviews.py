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
        required=False,
        help_text=_(
            "Выберите отзывы для отображения. Если список пуст, будут показаны все одобренные отзывы."
        ),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        from cms.forms import ReviewForm
        from cms.models.reviews import Review

        reviews = value.get("reviews")
        if not reviews:
            reviews = Review.objects.filter(is_approved=True).order_by("-date", "-id")

        context["reviews_list"] = reviews
        context["review_form"] = ReviewForm()
        return context

    class Meta:
        label = _("Блок отзывов")
        template = "cms/home/blocks/reviews.html"
        icon = "comment"
