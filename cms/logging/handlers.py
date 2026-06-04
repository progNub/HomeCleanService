import logging
import html


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
                meta = request.META
                ip = (
                    meta.get("HTTP_X_FORWARDED_FOR", meta.get("REMOTE_ADDR", "unknown"))
                    .split(",")[0]
                    .strip()
                )

                message_parts.append(
                    f"<b>🌐 Request:</b>\n"
                    f"🔹 <b>URL:</b> {escape_html(request.build_absolute_uri())}\n"
                    f"🔹 <b>Method:</b> {request.method}\n"
                    f"🔹 <b>User:</b> {escape_html(str(user))}\n"
                    f"🔹 <b>IP:</b> <code>{ip}</code>"
                )
            except Exception:
                pass

        # 2. Log message text
        emoji = self._get_level_emoji(record.levelno)
        clean_msg = record.getMessage()
        message_parts.append(
            f"{emoji} <b>{record.levelname}</b>\n{escape_html(clean_msg)}"
        )

        # 3. Traceback
        if record.exc_info:
            exc_text = logging.Formatter().formatException(record.exc_info)
            if len(exc_text) > 3000:
                exc_text = exc_text[:3000] + "\n... [Traceback truncated]"

            message_parts.append(
                f"<b>📜 Traceback:</b>\n<pre>{escape_html(exc_text)}</pre>"
            )

        return "\n\n".join(message_parts)

    def emit(self, record):
        try:
            formatted_message = self.format_message(record)
            self.tg.send_raw(formatted_message)
        except Exception:
            self.handleError(record)
