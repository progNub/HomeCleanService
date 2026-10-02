from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base.blocks import BaseStructBlock


class ReviewsBlock(BaseStructBlock):
    title = blocks.CharBlock(required=True, label=_("Заголовок"), default=_("Отзывы наших клиентов"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        from cms.forms import ReviewForm
        from cms.models.reviews import Review

        context["reviews"] = Review.objects.filter(is_approved=True).order_by("-date", "-id")[:30]
        request = context.get("request")
        data = request.session.pop("review_form_data", None) if request and hasattr(request, "session") else None
        context["review_form"] = ReviewForm(data=data, request=request)
        if data is not None:
            request._wagtailcache_update = False
            request._wagtailcache_skip = True
        return context

    class Meta:
        label = _("Блок отзывов")
        template = "cms/home/blocks/reviews.html"
        icon = "comment"
