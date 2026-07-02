from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base.blocks import BaseStructBlock


class ReviewsBlock(BaseStructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок"), default=_("Отзывы наших клиентов"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        from cms.forms import ReviewForm
        from cms.models.reviews import Review

        context["reviews"] = Review.objects.filter(is_approved=True).order_by("-date", "-id")
        context["review_form"] = ReviewForm()
        return context

    class Meta:
        label = _("Блок отзывов")
        template = "cms/home/blocks/reviews.html"
        icon = "comment"
