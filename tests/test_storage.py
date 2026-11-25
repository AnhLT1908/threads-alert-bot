"""Test Storage SQLite: dedupe, state, failed messages."""

from app.storage import Storage


def test_mark_and_check_seen(tmp_path):
    storage = Storage(tmp_path / "test.db")
    assert not storage.is_seen("post-1")
    storage.mark_seen("post-1", "free")
    assert storage.is_seen("post-1")
    storage.close()


def test_mark_seen_is_idempotent(tmp_path):
    storage = Storage(tmp_path / "test.db")
    storage.mark_seen("post-1", "free")
    storage.mark_seen("post-1", "sales")  # khong ghi de keyword
    row = storage._conn.execute(
        "SELECT keyword FROM seen_posts WHERE post_id = ?", ("post-1",)
    ).fetchone()
    assert row == ("free",)
    storage.close()


def test_state_get_set_and_overwrite(tmp_path):
    storage = Storage(tmp_path / "test.db")
    assert storage.get_state("since:free") is None
    storage.set_state("since:free", 100)
    assert storage.get_state("since:free") == 100
    storage.set_state("since:free", 200)
    assert storage.get_state("since:free") == 200
    storage.close()


def test_state_persists_across_connections(tmp_path):
    path = tmp_path / "test.db"
    storage = Storage(path)
    storage.set_state("since:free", 123)
    storage.close()

    reopened = Storage(path)
    assert reopened.get_state("since:free") == 123
    reopened.close()


def test_failed_messages_add_and_pop(tmp_path):
    storage = Storage(tmp_path / "test.db")
    storage.add_failed("111", "msg-1", "boom")
    storage.add_failed("111", "msg-2", "boom")

    popped = storage.pop_failed(limit=1)
    assert len(popped) == 1
    assert popped[0].text == "msg-1"
    assert popped[0].chat_id == "111"

    # msg-1 da bi xoa, con msg-2
    remaining = storage.pop_failed()
    assert len(remaining) == 1
    assert remaining[0].text == "msg-2"
    # bang da trong
    assert storage.pop_failed() == []
    storage.close()
