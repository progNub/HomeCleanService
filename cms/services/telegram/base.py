import logging
import requests
from io import BytesIO
from django.conf import settings
from django.tasks import task

logger = logging.getLogger(__name__)


@task()
def _send_telegram_message_task(
    token, chat_id, text, parse_mode, timeout, api_endpoint
):
    """
    Background task to send a message to Telegram.
    If the message is too long, it sends it as a document.
    """
    if not token:
        logger.error("Telegram bot token is missing")
        return

    url_base = f"{api_endpoint}/bot{token}"
    max_len = 4096

    try:
        if len(text) <= max_len:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            response = requests.post(
                f"{url_base}/sendMessage", json=payload, timeout=timeout
            )
        else:
            # If the message is too long, send it as a document
            caption = text[:1000]
            files = {"document": ("message.txt", BytesIO(text.encode()), "text/plain")}
            payload = {
                "chat_id": chat_id,
                "caption": caption,
            }
            response = requests.post(
                f"{url_base}/sendDocument", data=payload, files=files, timeout=timeout
            )
        response.raise_for_status()
    except Exception:
        logger.exception("Error sending Telegram message via task")


class RawTelegramService:
    """
    Basic service for sending messages to Telegram via background tasks.
    """

    API_ENDPOINT = "https://api.telegram.org"

    def __init__(
        self, token=None, chat_id=None, parse_mode="HTML", timeout=10, queue_name=None
    ):
        self.token = token or getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.chat_id = chat_id or getattr(
            settings, "TELEGRAM_NOTIFICATIONS_CHAT_ID", None
        )
        self.parse_mode = parse_mode
        self.timeout = timeout
        self.queue_name = queue_name

    def send_raw(self, text, chat_id=None):
        """
        Enqueues a Telegram message for delivery.
        """
        target_chat_id = chat_id or self.chat_id
        if not self.token or not target_chat_id:
            logger.warning("Token or chat_id is missing for Telegram notification")
            return

        params = {
            "token": self.token,
            "chat_id": target_chat_id,
            "text": str(text),
            "parse_mode": self.parse_mode,
            "timeout": self.timeout,
            "api_endpoint": self.API_ENDPOINT,
        }

        if self.queue_name:
            _send_telegram_message_task.using(queue_name=self.queue_name).enqueue(
                **params
            )
        else:
            _send_telegram_message_task.enqueue(**params)
