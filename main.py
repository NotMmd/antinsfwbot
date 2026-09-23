"""PyroTGFork bot entry point."""

import logging

from config import Config
from classifier import ClassifierRouter
from db import Database
from jev import HttpJsonClassifier, JevClassifier, collect_payload
from settings import (
    SETTING_DEFAULTS,
    build_keyboard,
    get_actionable_verdict,
    is_admin_allowed,
    toggle_setting,
)

try:
    from pyrogram import Client, filters
except ImportError as exc:
    raise RuntimeError("Install dependencies with `pip install -r requirements.txt`") from exc


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("antinsfwbot")
config = Config.from_env()
database = Database(config.database_path)
classifier = ClassifierRouter({
    "jev": JevClassifier(config.jev_api_url, config.jev_api_key),
    "laya": HttpJsonClassifier(config.laya_api_url, config.laya_api_key),
})
app = Client(
    "antinsfwbot",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
)


def allowed(user_id: int | None) -> bool:
    return is_admin_allowed(config.admin_ids, user_id)


@app.on_message(filters.command("settings"))
async def show_settings(client, message):
    user_id = message.from_user.id if message.from_user else None
    if not allowed(user_id):
        await message.reply_text("You are not allowed to change bot settings.")
        return
    await message.reply_text(
        "Comment moderation settings:",
        reply_markup=build_keyboard(database, user_id, config.system_one_engine),
    )


@app.on_callback_query(filters.regex(r"^setting:toggle:"))
async def change_setting(client, query):
    try:
        _, _, key, requester = query.data.split(":", 3)
        requester_id = int(requester)
        if query.from_user.id != requester_id or not allowed(query.from_user.id):
            await query.answer("This settings panel belongs to another user.", show_alert=True)
            return
        toggle_setting(database, key, config.system_one_engine)
        await query.message.edit_reply_markup(
            build_keyboard(database, requester_id, config.system_one_engine)
        )
        await query.answer("Setting updated")
    except (ValueError, TypeError):
        await query.answer("Invalid setting", show_alert=True)


@app.on_message(filters.channel)
async def track_channel_post(client, message):
    preview = message.text or message.caption or ""
    database.track_post(message.chat.id, message.id, preview)


@app.on_message(filters.group & (filters.text | filters.caption))
async def classify_comment(client, message):
    sender = message.from_user
    if not sender or sender.is_bot or (message.text and message.text.startswith("/")):
        return
    chat_id, message_id = message.chat.id, message.id
    verdict = get_actionable_verdict(database, chat_id, message_id)
    if not database.get_setting("enabled", SETTING_DEFAULTS["enabled"]):
        return
    if verdict is None:
        try:
            payload = await collect_payload(client, message, database)
            engine = database.get_setting("system_one_engine", config.system_one_engine)
            verdict = await classifier.classify(payload, engine)
            database.cache_verdict(chat_id, message_id, verdict)
        except Exception:
            logger.exception("Jev classification failed for %s/%s", chat_id, message_id)
            return
    if verdict and verdict.get("verdict", "").lower() in {"nsfw", "adult", "unsafe"}:
        if database.get_setting("delete_nsfw", SETTING_DEFAULTS["delete_nsfw"]):
            try:
                await message.delete()
            except Exception:
                logger.exception("Unable to delete classified comment %s/%s", chat_id, message_id)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
