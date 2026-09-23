"""Runtime setting defaults and inline keyboard helpers."""

from typing import Any

SETTING_LABELS = {
    "enabled": "Comment classification",
    "delete_nsfw": "Delete NSFW comments",
    "system_one_engine": "System One engine",
}
SETTING_DEFAULTS = {"enabled": True, "delete_nsfw": False, "system_one_engine": "jev"}


def is_admin_allowed(admin_ids: tuple[int, ...], user_id: int | None) -> bool:
    return user_id is not None and user_id in admin_ids


def get_actionable_verdict(database: Any, chat_id: int, message_id: int) -> dict[str, Any] | None:
    if not database.get_setting("enabled", SETTING_DEFAULTS["enabled"]):
        return None
    return database.get_verdict(chat_id, message_id)


def toggle_setting(database: Any, key: str, engine_default: str = "jev") -> bool | str:
    if key not in SETTING_LABELS:
        raise ValueError(f"Unknown setting: {key}")
    current = database.get_setting(key, engine_default if key == "system_one_engine" else SETTING_DEFAULTS[key])
    updated = ("laya" if current == "jev" else "jev") if key == "system_one_engine" else not bool(current)
    database.set_setting(key, updated)
    return updated


def build_keyboard(database: Any, requester_id: int, engine_default: str = "jev") -> Any:
    """Build a PyroTGFork inline keyboard from the current persisted values."""
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = []
    for key, label in SETTING_LABELS.items():
        value = database.get_setting(key, engine_default if key == "system_one_engine" else SETTING_DEFAULTS[key])
        state = value.upper() if key == "system_one_engine" else ("ON" if value else "OFF")
        rows.append([InlineKeyboardButton(
            f"{label}: {state}", callback_data=f"setting:toggle:{key}:{requester_id}"
        )])
    return InlineKeyboardMarkup(rows)
