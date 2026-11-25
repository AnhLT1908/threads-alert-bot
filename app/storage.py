"""Luu tru SQLite: dedupe bai da bao, state chu ky quet, tin nhan gui loi."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_posts (
    post_id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    notified_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS failed_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    text TEXT NOT NULL,
    error TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True, slots=True)
class FailedMessage:
    """Tin nhan canh bao da gui Telegram that bai, cho gui bu."""

    row_id: int
    chat_id: str
    text: str
    error: str
    created_at: str


class Storage:
    """SQLite don gian, chiu duoc tan suat nho cua bot ca nhan.

    Ghi dong bo trong vong lap async la chap nhan duoc vi moi chu ky
    chi thuc hien vai chuc thao tac.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- seen posts (dedupe) ---

    def is_seen(self, post_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,)
        ).fetchone()
        return row is not None

    def mark_seen(self, post_id: str, keyword: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen_posts (post_id, keyword, notified_at)"
            " VALUES (?, ?, ?)",
            (post_id, keyword, _utc_now()),
        )
        self._conn.commit()

    # --- state (since timestamp moi tu khoa) ---

    def get_state(self, key: str) -> int | None:
        row = self._conn.execute(
            "SELECT value FROM state WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        try:
            return int(row[0])
        except ValueError:
            return None

    def set_state(self, key: str, value: int) -> None:
        self._conn.execute(
            "INSERT INTO state (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        self._conn.commit()

    # --- failed messages (gui bu) ---

    def add_failed(self, chat_id: str, text: str, error: str) -> None:
        self._conn.execute(
            "INSERT INTO failed_messages (chat_id, text, error, created_at)"
            " VALUES (?, ?, ?, ?)",
            (chat_id, text, error, _utc_now()),
        )
        self._conn.commit()

    def pop_failed(self, limit: int = 10) -> list[FailedMessage]:
        """Lay va xoa cac tin nhan loi (theo thu tu cu nhat).

        Neu gui bu lai that bai, nguoi goi phai add_failed() lai.
        """
        rows = self._conn.execute(
            "SELECT id, chat_id, text, error, created_at"
            " FROM failed_messages ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        if not rows:
            return []

        ids = [row[0] for row in rows]
        placeholders = ",".join("?" * len(ids))
        self._conn.execute(
            f"DELETE FROM failed_messages WHERE id IN ({placeholders})", ids
        )
        self._conn.commit()
        return [FailedMessage(*row) for row in rows]
