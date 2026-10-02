import html
import logging

from cms.request_utils import get_client_ip


def escape_html(text):
    return html.escape(str(text), quote=False)


class AsyncTelegramHandler(logging.Handler):
    """
    Handler for sending logs to Telegram using RawTelegramService.
    Message formatting occurs directly in the handler.
    """

    def __init__(
        self,
        token,
        chat_id,
        level=logging.NOTSET,
        timeout=10,
        disable_notification=False,
        disable_web_page_preview=False,
    ):
        super().__init__(level=level)
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self.disable_notification = disable_notification
        self.disable_web_page_preview = disable_web_page_preview
        self._tg = None

    @property
    def tg(self):
        if self._tg is None:
            from cms.services.telegram.base import RawTelegramService

            self._tg = RawTelegramService(
                token=self.token,
                chat_id=self.chat_id,
                timeout=self.timeout,
                parse_mode="HTML",
                queue_name="notifications",
            )
        return self._tg

    def _get_level_emoji(self, levelno):
        if levelno >= logging.CRITICAL:
            return "🚨"
        if levelno >= logging.ERROR:
            return "❌"
        if levelno >= logging.WARNING:
            return "⚠️"
        return "ℹ️"

    def format_message(self, record):
        """
        Formats the HTML message in the order: Request -> Message -> Traceback.
        """
        message_parts = []

        # 1. Request information
        request = getattr(record, "request", None)
        if request:
            try:
                user = getattr(request, "user", "Anonymous")
                ip = get_client_ip(request) or "unknown"

                message_parts.append(
                    f"<b>🌐 Request:</b>\n"
                    f"🔹 <b>Path:</b> {escape_html(request.path)}\n"
                    f"🔹 <b>Method:</b> {request.method}\n"
                    f"🔹 <b>User:</b> {escape_html(str(user))}\n"
                    f"🔹 <b>IP:</b> <code>{ip}</code>"
                )
            except Exception:
                pass

        # 2. Log message text
        emoji = self._get_level_emoji(record.levelno)
        clean_msg = self._redact(record.getMessage())
        message_parts.append(f"{emoji} <b>{record.levelname}</b>\n{escape_html(clean_msg)}")

        # 3. Traceback
        if record.exc_info:
            # Application traceback text may include request data and secrets.
            exc_text = f"{record.exc_info[0].__name__}: inspect server logs for details"
            if len(exc_text) > 3000:
                exc_text = exc_text[:3000] + "\n... [Traceback truncated]"

            message_parts.append(f"<b>📜 Traceback:</b>\n<pre>{escape_html(exc_text)}</pre>")

        return "\n\n".join(message_parts)

    def emit(self, record):
        if record.name.startswith(("cms.services.telegram", "django_tasks", "django_tasks_db")):
            return
        try:
            formatted_message = self.format_message(record)
            self.tg.send_raw(formatted_message)
        except Exception:
            # handleError prints raw record/traceback and can leak request data.
            return

    def _redact(self, message):
        return message.replace(self.token, "[redacted]") if self.token else message
