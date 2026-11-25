"""Format va gui canh bao qua Telegram Bot API."""

import asyncio
import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

from app.threads_client import ThreadPost

logger = logging.getLogger(__name__)

TEXT_PREVIEW_LENGTH = 280
DISPLAY_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SEND_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 2.0


def format_alert_text(keyword: str, post: ThreadPost) -> str:
    """Dinh dang noi dung tin nhan canh bao (HTML parse mode).

    Toan bo noi dung tu bai viet deu qua html.escape() de tranh HTML
    injection; chu dong HTML chi la the <b> cua tieu de.
    """
    preview = post.text.strip()
    if len(preview) > TEXT_PREVIEW_LENGTH:
        preview = preview[:TEXT_PREVIEW_LENGTH].rstrip() + "…"

    if post.timestamp_unix() > 0:
        ts = datetime.fromtimestamp(post.timestamp_unix(), tz=DISPLAY_TZ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        ts = post.timestamp

    lines = [
        f'🔔 Trùng từ khóa: <b>"{html.escape(keyword)}"</b>',
        f"👤 @{html.escape(post.username)}",
        f"🕐 {ts} (UTC+7)",
        "",
        html.escape(preview),
    ]
    return "\n".join(lines)


def build_open_button(post: ThreadPost) -> InlineKeyboardMarkup | None:
    """Nut inline mo bai viet tren Threads. None neu khong co permalink."""
    if not post.permalink:
        return None
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Mở trên Threads", url=post.permalink)
    )


class TelegramNotifier:
    """Gui tin nhan (dang HTML) ve 1 chat Telegram co dinh."""

    def __init__(self, bot: Bot, chat_id: str) -> None:
        self._bot = bot
        self._chat_id = chat_id

    @classmethod
    async def create(cls, token: str, chat_id: str) -> "TelegramNotifier":
        """Tao Bot va initialize truoc khi dung (PTB v21 bat buoc)."""
        bot = Bot(token)
        await bot.initialize()
        return cls(bot, chat_id)

    async def aclose(self) -> None:
        await self._bot.shutdown()

    async def send(
        self,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        """Gui tin nhan, retry exponential backoff.

        Raises:
            TelegramError: sau SEND_RETRIES lan thu that bai.
        """
        last_error: TelegramError | None = None
        for attempt in range(SEND_RETRIES):
            try:
                await self._bot.send_message(
                    chat_id=self._chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                )
                return
            except TelegramError as exc:
                last_error = exc
                if attempt < SEND_RETRIES - 1:
                    delay = RETRY_BASE_DELAY_SECONDS * (2**attempt)
                    logger.warning(
                        "Gui Telegram loi (lan %d/%d), thu lai sau %.1fs: %s",
                        attempt + 1,
                        SEND_RETRIES,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error
