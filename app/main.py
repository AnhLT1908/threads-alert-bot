"""Entrypoint cua bot.

W1: chi nap config va in ra de kiem tra scaffold.
Cac task W2-W6 se noi pipeline day du vao day.
"""

import asyncio
import logging
import sys

from app.config import Settings
from app.keywords import load_keywords
from app.scheduler import compute_poll_interval

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


async def main() -> None:
    settings = Settings()
    keywords = load_keywords(settings.keywords_path)
    interval = compute_poll_interval(len(keywords), settings.poll_interval_minutes)

    missing = settings.validate_tokens()
    if missing:
        logger.warning("Thieu cau hinh: %s", ", ".join(missing))

    logger.info("Threads Alert Bot khoi dong")
    logger.info("So tu khoa: %d -> %s", len(keywords), keywords)
    logger.info("Chu ky quet: %d phut", interval)
    logger.info("Chat ID Telegram: %s", settings.telegram_chat_id or "(chua cau hinh)")


if __name__ == "__main__":
    asyncio.run(main())
