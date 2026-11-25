"""Test Telegram notifier: format, escape HTML, retry."""

import pytest
from telegram.error import TelegramError

from app.notifier import (
    TelegramNotifier,
    build_open_button,
    format_alert_text,
)
from app.threads_client import ThreadPost


def make_post(text: str = "hello", permalink: str = "https://threads.com/@u/post/1"):
    return ThreadPost(
        post_id="1",
        text=text,
        media_type="TEXT_POST",
        permalink=permalink,
        timestamp="2026-11-25T05:42:03+0000",
        username="u",
    )


def test_format_alert_contains_keyword_and_username():
    text = format_alert_text("miễn phí AI", make_post("Hoc mien phi AI ngay"))
    assert "miễn phí AI" in text
    assert "@u" in text
    assert "Hoc mien phi AI ngay" in text


def test_format_alert_escapes_html_in_user_content():
    text = format_alert_text("free", make_post("<b>bold</b> & <i>hack</i>"))
    assert "<b>bold</b>" not in text
    assert "&lt;b&gt;bold&lt;/b&gt;" in text
    assert "&lt;i&gt;hack&lt;/i&gt;" in text


def test_format_alert_escapes_html_in_keyword():
    text = format_alert_text("<script>", make_post("post"))
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


def test_format_alert_truncates_long_preview():
    long_text = "x" * 300
    text = format_alert_text("free", make_post(long_text))
    assert "…" in text
    # doan preview khong vuot 280 ky tu + dau ellipsis
    preview_line = text.splitlines()[-1]
    assert len(preview_line) == 281


def test_format_alert_shows_vietnam_time():
    # 05:42 UTC => 12:42 UTC+7
    text = format_alert_text("free", make_post())
    assert "12:42:03" in text
    assert "UTC+7" in text


def test_build_open_button_with_permalink():
    markup = build_open_button(make_post())
    assert markup is not None
    button = markup.inline_keyboard[0][0]
    assert button.text == "Mở trên Threads"
    assert button.url == "https://threads.com/@u/post/1"


def test_build_open_button_without_permalink():
    post = make_post(permalink="")
    assert build_open_button(post) is None


class FakeBot:
    def __init__(self, fail_times: int = 0):
        self.fail_times = fail_times
        self.calls: list[dict] = []

    async def send_message(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_times > 0:
            self.fail_times -= 1
            raise TelegramError("flaky network")
        return None


async def test_send_succeeds_first_try():
    bot = FakeBot()
    notifier = TelegramNotifier(bot, "123")
    await notifier.send("chao")
    assert len(bot.calls) == 1
    assert bot.calls[0]["chat_id"] == "123"
    assert bot.calls[0]["parse_mode"] is not None


async def test_send_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("app.notifier.RETRY_BASE_DELAY_SECONDS", 0.0)
    bot = FakeBot(fail_times=2)
    notifier = TelegramNotifier(bot, "123")
    await notifier.send("chao")
    assert len(bot.calls) == 3  # 2 fail + 1 thanh cong


async def test_send_raises_after_all_retries(monkeypatch):
    monkeypatch.setattr("app.notifier.RETRY_BASE_DELAY_SECONDS", 0.0)
    bot = FakeBot(fail_times=99)
    notifier = TelegramNotifier(bot, "123")
    with pytest.raises(TelegramError):
        await notifier.send("chao")
    assert len(bot.calls) == 3
