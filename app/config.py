"""Cau hinh ung dung, nap tu file .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Toan bo cau hinh cua bot.

    Gia tri nap tu bien moi truong / file .env (pydantic-settings).
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Threads Graph API
    threads_access_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Chu ky quet (phut). None = tu dong tinh theo so tu khoa.
    poll_interval_minutes: int | None = None

    # Duong dan
    data_dir: Path = PROJECT_ROOT / "data"
    keywords_path: Path = PROJECT_ROOT / "keywords.json"

    def validate_tokens(self) -> list[str]:
        """Tra ve danh sach thieu sot cau hinh (rỗng = hop le)."""
        missing = []
        if not self.threads_access_token:
            missing.append("THREADS_ACCESS_TOKEN")
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        return missing
