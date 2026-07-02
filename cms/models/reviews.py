import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

from cms.services.telegram.notifications import LeadNotificationService

logger = logging.getLogger(__name__)


@register_snippet
class Review(models.Model):
    author = models.CharField(max_length=255, verbose_name=_("Автор"))
    text = models.TextField(verbose_name=_("Текст отзыва"), max_length=2000)
    rating = models.PositiveSmallIntegerField(
        default=5, choices=[(i, str(i)) for i in range(1, 6)], verbose_name=_("Рейтинг")
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата и время"))

    accept_privacy = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        verbose_name=_("Согласие на обработку персональных данных"),
    )

    is_approved = models.BooleanField(default=False, verbose_name=_("Одобрено (показывать)"))
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP-адрес"))
    user_agent = models.TextField(null=True, blank=True, verbose_name=_("User-Agent"))

    panels = [
        FieldPanel("author"),
        FieldPanel("text"),
        FieldPanel("rating"),
        FieldPanel("accept_privacy", read_only=True),
        FieldPanel("is_approved"),
        FieldPanel("ip", read_only=True),
        FieldPanel("user_agent", read_only=True),
    ]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.notify_new_review()

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")

    def __str__(self):
        is_approved_msg = _("Одобрено") if self.is_approved else _("Не одобрено")
        return f"{self.author} - {self.rating} ({is_approved_msg})"

    def notify_new_review(self):
        """
        Sends notification about new review using LeadNotificationService.
        """
        try:
            service = LeadNotificationService(self)
            service.send()
        except Exception:
            logger.exception(_("Error sending review notification to Telegram"))
