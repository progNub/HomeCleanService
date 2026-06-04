import requests
import logging
from django.conf import settings
from django_tasks import task

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """
    Service for sending notifications to Telegram using Django Tasks.
    """

    API_ENDPOINT = "https://api.telegram.org"

    @staticmethod
    @task(queue_name="notification")
    def _send_message_task(chat_id, text, parse_mode="HTML"):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN is not set")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram message sent successfully")
        except Exception:
            logger.exception("Error sending Telegram message")

    def send(self, text, chat_id=None, parse_mode="HTML"):
        """
        Sends a message to Telegram via background task.
        """
        if chat_id is None:
            chat_id = settings.TELEGRAM_NOTIFICATIONS_CHAT_ID

        if not chat_id:
            logger.warning("Telegram chat_id is not provided and not set in settings")
            return

        self._send_message_task.enqueue(
            chat_id=chat_id, text=text, parse_mode=parse_mode
        )
