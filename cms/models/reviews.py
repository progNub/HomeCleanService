from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Review(models.Model):
    author = models.CharField(max_length=255, verbose_name=_("Автор"))
    text = models.TextField(verbose_name=_("Текст отзыва"))
    rating = models.PositiveSmallIntegerField(
        default=5, choices=[(i, str(i)) for i in range(1, 6)], verbose_name=_("Рейтинг")
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата и время"))
    is_approved = models.BooleanField(
        default=True, verbose_name=_("Одобрено (показывать)")
    )
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP-адрес"))
    user_agent = models.TextField(null=True, blank=True, verbose_name=_("User-Agent"))

    panels = [
        FieldPanel("author"),
        FieldPanel("text"),
        FieldPanel("rating"),
        FieldPanel("is_approved"),
        FieldPanel("ip", read_only=True),
        FieldPanel("user_agent", read_only=True),
    ]

    def __str__(self):
        return f"{self.author} - {self.rating}"

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")
