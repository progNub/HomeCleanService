import logging
from io import BytesIO

import requests
from django.conf import settings
from django.db import transaction
from django.tasks import task

logger = logging.getLogger(__name__)


class TelegramDeliveryError(Exception):
    """Safe error persisted by the task backend without provider URLs or payloads."""


@task()
def _send_telegram_message_task(
    token=None, chat_id=None, text="", parse_mode="HTML", timeout=10, api_endpoint="https://api.telegram.org"
):
    """
    Background task to send a message to Telegram.
    If the message is too long, it sends it as a document.
    """
    # The optional token argument preserves compatibility with already queued jobs.
    # New jobs resolve credentials at execution and never persist them in kwargs.
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None) or token
    if not token:
        raise TelegramDeliveryError("Telegram credentials are not configured")

    url_base = f"{api_endpoint}/bot{token}"
    max_len = 4096

    try:
        if len(text) <= max_len:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            response = requests.post(f"{url_base}/sendMessage", json=payload, timeout=timeout)
        else:
            # If the message is too long, send it as a document
            caption = text[:1000]
            files = {"document": ("message.txt", BytesIO(text.encode()), "text/plain")}
            payload = {
                "chat_id": chat_id,
                "caption": caption,
            }
            response = requests.post(f"{url_base}/sendDocument", data=payload, files=files, timeout=timeout)

        if not response.ok:
            raise TelegramDeliveryError(f"Telegram delivery failed (HTTP {response.status_code})")
        if response.json().get("ok") is not True:
            raise TelegramDeliveryError("Telegram rejected delivery")
    except (requests.RequestException, ValueError):
        # Suppress chained requests exceptions: their text contains the bot token URL.
        raise TelegramDeliveryError("Telegram transport or response failure") from None


class RawTelegramService:
    """
    Basic service for sending messages to Telegram via background tasks.
    """

    API_ENDPOINT = "https://api.telegram.org"

    def __init__(self, token=None, chat_id=None, parse_mode="HTML", timeout=10, queue_name=None):
        self.token = token or getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.chat_id = chat_id or getattr(settings, "TELEGRAM_NOTIFICATIONS_CHAT_ID", None)
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
            "chat_id": target_chat_id,
            "text": str(text),
            "parse_mode": self.parse_mode,
            "timeout": self.timeout,
            "api_endpoint": self.API_ENDPOINT,
        }

        def enqueue():
            try:
                task_to_send = _send_telegram_message_task
                if self.queue_name:
                    task_to_send = task_to_send.using(queue_name=self.queue_name)
                task_to_send.enqueue(**params)
            except Exception:
                # Notification failure must not discard an already saved lead.
                logger.error("Telegram notification could not be queued; inspect saved submissions")

        transaction.on_commit(enqueue)
