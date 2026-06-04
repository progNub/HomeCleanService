import logging
from django.conf import settings
from django.utils.translation import gettext as _
from .base import RawTelegramService

logger = logging.getLogger(__name__)


class LeadNotificationService:
    """
    Business service for processing and sending notifications based on model instances.
    """

    def __init__(self, instance=None):
        self.instance = instance
        self.chat_id = getattr(settings, "TELEGRAM_NOTIFICATIONS_CHAT_ID", None)
        self._tg = None

    @property
    def tg(self):
        if self._tg is None:
            self._tg = RawTelegramService(
                chat_id=self.chat_id, parse_mode="HTML", queue_name="notifications"
            )
        return self._tg

    def send(self, instance=None):
        """
        Main send method. If instance is not passed to the method,
        the one passed during initialization is used.
        """
        obj = instance or self.instance
        if not obj:
            logger.error(_("No instance provided for notification."))
            return

        if not self.chat_id:
            logger.warning(_("TELEGRAM_NOTIFICATIONS_CHAT_ID is not configured."))
            return

        message = self._get_message(obj)
        if message:
            self.tg.send_raw(message)

    def _get_message(self, instance):
        """Determines the instance type and returns the formatted text."""
        model_name = instance.__class__.__name__
        handler = getattr(self, f"_format_{model_name.lower()}", None)

        if handler:
            return handler(instance)

        logger.error(
            _("Unsupported model type for Telegram alerts: %(model_name)s")
            % {"model_name": model_name}
        )
        return None

    def _format_review(self, review):
        """Formatting message for Review model"""
        text = getattr(review, "text", "") or ""
        truncated_text = text[:200] + "..." if len(text) > 200 else text

        return (
            f"🌟 <b>{_('Новый отзыв на сайте!')}</b>\n\n"
            f"👤 <b>{_('Автор')}:</b> {getattr(review, 'author', _('Аноним'))}\n"
            f"⭐ <b>{_('Рейтинг')}:</b> {getattr(review, 'rating', '?')}/5\n"
            f"📝 <b>{_('Текст')}:</b> <i>{truncated_text}</i>"
        )

    def _format_formsubmission(self, submission):
        """Formatting message for FormSubmission model (Wagtail)"""
        page = getattr(submission, "page", None)
        form_data = getattr(submission, "form_data", {})
        title = getattr(page, "title", _("с формы"))

        message = f"📋 <b>{_('Новая заявка')}: {title}</b>\n\n"

        if page and hasattr(page, "form_fields"):
            for field in page.form_fields.all():
                value = form_data.get(field.clean_name)
                if value:
                    if isinstance(value, list):
                        value = ", ".join(map(str, value))
                    message += f"🔹 <b>{field.label}:</b> {value}\n"
        else:
            for key, value in form_data.items():
                message += f"🔹 <b>{key}:</b> {value}\n"

        return message
