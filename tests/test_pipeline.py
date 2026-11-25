"""Integration test pipeline: run_cycle + flush_failed voi fake dependency."""

from telegram.error import TelegramError

from app.main import flush_failed, run_cycle
from app.storage import Storage
from app.threads_client import ThreadPost, ThreadsApiError

NOW = 1_768_000_000


def make_post(post_id: str, text: str) -> ThreadPost:
    return ThreadPost(
        post_id=post_id,
        text=text,
        media_type="TEXT_POST",
        permalink=f"https://threads.com/@u/post/{post_id}",
        timestamp="2026-11-25T05:42:03+0000",
        username="u",
    )


class FakeThreadsClient:
    def __init__(self, results: dict[str, list[ThreadPost]]):
        self._results = results
        self.calls: list[str] = []

    async def keyword_search(self, keyword, since_unix=None, limit=100):
        self.calls.append(keyword)
        return self._results.get(keyword, [])


class FailingClient:
    async def keyword_search(self, keyword, since_unix=None, limit=100):
        raise ThreadsApiError(f"loi gia lap khi search {keyword}")


class FakeNotifier:
    def __init__(self, fail_times: int = 0):
        self.sent: list[str] = []
        self._fail_times = fail_times
        self.chat_id = "123456"

    async def send(self, text, reply_markup=None):
        if self._fail_times > 0:
            self._fail_times -= 1
            raise TelegramError("loi gia lap")
        self.sent.append(text)


async def test_run_cycle_sends_only_new_matching_posts(tmp_path):
    storage = Storage(tmp_path / "test.db")
    notifier = FakeNotifier()
    client = FakeThreadsClient(
        {
            "promote": [
                make_post("1", "Promote your AI course free today"),
                make_post("2", "promote ban hang sieu re"),
                make_post("3", "bai viet khong lien quan gi ca"),
            ]
        }
    )
    # bai 2 da bao truoc do
    storage.mark_seen("2", "promote")

    await run_cycle(client, storage, notifier, ["promote"], NOW)

    assert len(notifier.sent) == 1
    assert "Promote your AI course" in notifier.sent[0]
    # bai 1 gio la seen
    assert storage.is_seen("1")
    # state since duoc cap nhat (tru overlap 60s)
    assert storage.get_state("since:promote") == NOW - 60
    storage.close()


async def test_run_cycle_does_not_resend_seen_posts(tmp_path):
    storage = Storage(tmp_path / "test.db")
    notifier = FakeNotifier()
    post = make_post("1", "free course now")

    client = FakeThreadsClient({"free": [post]})
    await run_cycle(client, storage, notifier, ["free"], NOW)
    await run_cycle(client, storage, notifier, ["free"], NOW + 600)

    assert len(notifier.sent) == 1
    storage.close()


async def test_run_cycle_survives_api_error(tmp_path):
    storage = Storage(tmp_path / "test.db")
    notifier = FakeNotifier()
    client = FailingClient()

    await run_cycle(client, storage, notifier, ["free"], NOW)

    assert notifier.sent == []
    assert storage.get_state("since:free") is None
    storage.close()


async def test_flush_failed_resends_and_keeps_failures(tmp_path):
    storage = Storage(tmp_path / "test.db")
    storage.add_failed("123456", "canh bao 1", "err")
    storage.add_failed("123456", "canh bao 2", "err")

    # lan gui dau tien loi, cac lan sau thanh cong
    notifier = FakeNotifier(fail_times=1)
    await flush_failed(storage, notifier)

    assert notifier.sent == ["canh bao 2"]
    remaining = storage.pop_failed()
    assert len(remaining) == 1
    assert remaining[0].text == "canh bao 1"
    storage.close()
