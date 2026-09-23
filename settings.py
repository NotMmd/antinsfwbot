"""SQLite-backed moderation settings with environment-based defaults."""

import os
import sqlite3
from contextlib import contextmanager


DEFAULT_SETTINGS = {
    "auto_ban": False,
    "auto_delete": True,
    "ban_scope": "group",
    "notify_admin": True,
}

_ENV_KEYS = {
    "auto_ban": "AUTO_BAN",
    "auto_delete": "AUTO_DELETE",
    "ban_scope": "BAN_SCOPE",
    "notify_admin": "NOTIFY_ADMIN",
}
_SCOPES = {"group", "channel", "both"}


def _instance_key(group_id, channel_id):
    return f"{group_id}:{channel_id}"


def _db_path(db_path):
    return os.path.expanduser(db_path or os.getenv("DB_PATH", "~/antinsfwbot/posts.db"))


@contextmanager
def _connect(db_path):
    path = _db_path(db_path)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _ensure_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            instance_key TEXT NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            PRIMARY KEY (instance_key, setting_key)
        )
        """
    )


def _as_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Expected a boolean value, got {value!r}")


def _environment_defaults():
    values = DEFAULT_SETTINGS.copy()
    for key, env_key in _ENV_KEYS.items():
        raw = os.getenv(env_key)
        if raw is None:
            continue
        if key == "ban_scope":
            value = raw.strip().lower()
            if value not in _SCOPES:
                raise ValueError(f"{env_key} must be one of: group, channel, both")
            values[key] = value
        else:
            values[key] = _as_bool(raw)
    return values


def get_settings(db_path=None, group_id=None, channel_id=None):
    """Return the effective settings, using SQLite overrides over env defaults."""
    values = _environment_defaults()
    with _connect(db_path) as conn:
        _ensure_table(conn)
        rows = conn.execute(
            "SELECT setting_key, setting_value FROM settings WHERE instance_key = ?",
            (_instance_key(group_id, channel_id),),
        ).fetchall()

    for key, value in rows:
        if key in {"auto_ban", "auto_delete", "notify_admin"}:
            values[key] = _as_bool(value)
        elif key == "ban_scope" and value in _SCOPES:
            values[key] = value
    return values


def set_setting(key, value, db_path=None, group_id=None, channel_id=None):
    """Persist one validated setting for the configured group/channel pair."""
    if key not in DEFAULT_SETTINGS:
        raise KeyError(key)
    if key == "ban_scope":
        normalized = str(value).strip().lower()
        if normalized not in _SCOPES:
            raise ValueError("ban_scope must be one of: group, channel, both")
    else:
        normalized = _as_bool(value)

    with _connect(db_path) as conn:
        _ensure_table(conn)
        conn.execute(
            """
            INSERT INTO settings (instance_key, setting_key, setting_value)
            VALUES (?, ?, ?)
            ON CONFLICT(instance_key, setting_key)
            DO UPDATE SET setting_value = excluded.setting_value
            """,
            (_instance_key(group_id, channel_id), key, str(normalized).lower()),
        )
