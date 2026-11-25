"""Entrypoint cua bot: scheduler poll tu khoa -> canh bao Telegram."""

import asyncio
import logging
import sys
import time

from telegram.error import TelegramError

from app.config import Settings
from app.keywords import load_keywords
from app.matcher import text_matches
from app.notifier import TelegramNotifier, build_open_button, format_alert_text
from app.scheduler import compute_poll_interval
from app.storage import Storage
from app.threads_client import ThreadsApiError, ThreadsClient

# Console Windows (cmd/PowerShell) thuong dung codepage cp1252/cp437
# khong hien thi duoc UTF-8. Ep output sang UTF-8 de log tieng Viet
# khong bi mojibake, va khong crash UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Chong lan 60s giua cac chu ky de khong bo sot bai dang dung luc quet.
# Dedupe qua seen_posts se loai bai trung.
SINCE_OVERLAP_SECONDS = 60
FAILED_FLUSH_LIMIT = 10


async def run_cycle(
    client: ThreadsClient,
    storage: Storage,
    notifier: TelegramNotifier,
    keywords: list[str],
    now_unix: int,
) -> None:
    """Quet 1 vong toan bo tu khoa: search -> matcher -> dedupe -> gui."""
    since_next = max(0, now_unix - SINCE_OVERLAP_SECONDS)

    for keyword in keywords:
        since = storage.get_state(f"since:{keyword}")
        try:
            posts = await client.keyword_search(keyword, since_unix=since)
        except ThreadsApiError as exc:
            logger.error("Keyword %r: %s", keyword, exc)
            continue

        for post in posts:
            if not text_matches(post.text, keyword):
                continue
            if storage.is_seen(post.post_id):
                continue

            storage.mark_seen(post.post_id, keyword)
            text = format_alert_text(keyword, post)
            try:
                await notifier.send(text, build_open_button(post))
                logger.info("Da canh bao %s (%s)", post.post_id, keyword)
            except TelegramError as exc:
                logger.error("Gui canh bao that bai %s: %s", post.post_id, exc)
                storage.add_failed(
                    notifier.chat_id, text, str(exc)
                )

        storage.set_state(f"since:{keyword}", since_next)


async def flush_failed(storage: Storage, notifier: TelegramNotifier) -> None:
    """Gui bu cac canh bao truoc day gui Telegram that bai."""
    for msg in storage.pop_failed(FAILED_FLUSH_LIMIT):
        try:
            await notifier.send(msg.text)
            logger.info("Gui bu canh bao #%d thanh cong", msg.row_id)
        except TelegramError as exc:
            logger.error("Gui bu canh bao #%d van loi: %s", msg.row_id, exc)
            storage.add_failed(msg.chat_id, msg.text, str(exc))


async def main() -> None:
    settings = Settings()

    missing = settings.validate_tokens()
    if missing:
        logger.error(
            "Thieu cau hinh bat buoc: %s. Xem .env.example", ", ".join(missing)
        )
        return

    keywords = load_keywords(settings.keywords_path)
    if not keywords:
        logger.error("Khong co tu khoa nao trong %s", settings.keywords_path)
        return

    interval = compute_poll_interval(
        len(keywords), settings.poll_interval_minutes
    )
    storage = Storage(settings.data_dir / "threads_alert.db")
    notifier = await TelegramNotifier.create(
        settings.telegram_bot_token, settings.telegram_chat_id
    )
    client = ThreadsClient(settings.threads_access_token)

    logger.info("Threads Alert Bot khoi dong")
    logger.info("So tu khoa: %d -> %s", len(keywords), keywords)
    logger.info("Chu ky quet: %d phut", interval)

    try:
        await notifier.send(
            "🤖 Bot theo doi Threads da chay.\n"
            f"Tu khoa ({len(keywords)}): {', '.join(keywords)}\n"
            f"Chu ky quet: {interval} phut"
        )
    except TelegramError as exc:
        logger.error("Khong gui duoc thong bao khoi dong: %s", exc)

    try:
        while True:
            await run_cycle(
                client, storage, notifier, keywords, int(time.time())
            )
            await flush_failed(storage, notifier)
            await asyncio.sleep(interval * 60)
    except asyncio.CancelledError:
        logger.info("Bot nhan tin hieu dung")
    finally:
        await client.aclose()
        await notifier.aclose()
        storage.close()


if __name__ == "__main__":
    asyncio.run(main())
