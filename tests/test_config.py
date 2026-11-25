"""Test validate cau hinh bat buoc."""

from app.config import Settings


def test_validate_tokens_lists_all_missing():
    settings = Settings(_env_file=None)
    missing = settings.validate_tokens()
    assert "THREADS_ACCESS_TOKEN" in missing
    assert "TELEGRAM_BOT_TOKEN" in missing
    assert "TELEGRAM_CHAT_ID" in missing


def test_validate_tokens_returns_empty_when_complete():
    settings = Settings(
        _env_file=None,
        threads_access_token="t",
        telegram_bot_token="b",
        telegram_chat_id="c",
    )
    assert settings.validate_tokens() == []


def test_blank_poll_interval_becomes_none():
    settings = Settings(_env_file=None, poll_interval_minutes="")
    assert settings.poll_interval_minutes is None


def test_poll_interval_parses_integer():
    settings = Settings(_env_file=None, poll_interval_minutes="7")
    assert settings.poll_interval_minutes == 7
