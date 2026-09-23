"""Small SQLite repository for runtime settings, posts, and verdicts."""

import json
import sqlite3
import threading
from typing import Any


class Database:
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.lock = threading.RLock()
        with self.lock, self.connection:
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS posts (
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    preview TEXT NOT NULL,
                    PRIMARY KEY (chat_id, message_id)
                );
                CREATE TABLE IF NOT EXISTS verdicts (
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    verdict_json TEXT NOT NULL,
                    PRIMARY KEY (chat_id, message_id)
                );
            """)

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.lock:
            row = self.connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return default if row is None else json.loads(row[0])

    def set_setting(self, key: str, value: Any) -> None:
        encoded = json.dumps(value)
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, encoded),
            )

    def track_post(self, chat_id: int, message_id: int, preview: str) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT INTO posts(chat_id, message_id, preview) VALUES(?, ?, ?) "
                "ON CONFLICT(chat_id, message_id) DO UPDATE SET preview = excluded.preview",
                (chat_id, message_id, preview or ""),
            )

    def get_post(self, chat_id: int, message_id: int) -> str | None:
        with self.lock:
            row = self.connection.execute(
                "SELECT preview FROM posts WHERE chat_id = ? AND message_id = ?", (chat_id, message_id)
            ).fetchone()
        return None if row is None else row[0]

    def cache_verdict(self, chat_id: int, message_id: int, verdict: dict[str, Any]) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT INTO verdicts(chat_id, message_id, verdict_json) VALUES(?, ?, ?) "
                "ON CONFLICT(chat_id, message_id) DO UPDATE SET verdict_json = excluded.verdict_json",
                (chat_id, message_id, json.dumps(verdict)),
            )

    def get_verdict(self, chat_id: int, message_id: int) -> dict[str, Any] | None:
        with self.lock:
            row = self.connection.execute(
                "SELECT verdict_json FROM verdicts WHERE chat_id = ? AND message_id = ?",
                (chat_id, message_id),
            ).fetchone()
        return None if row is None else json.loads(row[0])

    def close(self) -> None:
        with self.lock:
            self.connection.close()
