import html
import logging
import os
import sqlite3
from datetime import datetime, timezone

from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Configuration: reads from .env / environment variables with fallback values
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", "-1001234567890"))
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1001234567891"))
ADMIN_DM_ID = int(os.getenv("ADMIN_DM_ID", "123456789"))
WINDOW_MINUTES = int(os.getenv("WINDOW_MINUTES", "20"))
DB_PATH = os.path.expanduser(os.getenv("DB_PATH", "~/antinsfwbot/posts.db"))

HEART_EMOJIS_RAW = (
    "🩷", "❤️", "🧡", "💛", "💚", "🩵", "💙", "💜", "🖤", "🩶", "🤍", "🤎",
    "❤️‍🔥", "❤️‍🩹", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝",
)

_INVISIBLE = dict.fromkeys(map(ord, "\ufe0e\ufe0f\u200b\u200c\ufeff\u2060"), None)


def _normalize(text: str) -> str:
    return text.strip().translate(_INVISIBLE)


HEART_EMOJIS = frozenset(_normalize(e) for e in HEART_EMOJIS_RAW)


def is_single_heart(text: str) -> bool:
    if not text:
        return False
    return _normalize(text) in HEART_EMOJIS


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                msg_id INTEGER PRIMARY KEY,
                pub_date TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER PRIMARY KEY,
                pub_date TEXT
            )
            """
        )


def save_post(msg_id: int, dt: datetime):
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO posts (msg_id, pub_date) VALUES (?, ?)",
            (msg_id, dt.isoformat()),
        )


def save_thread(thread_id: int, dt: datetime):
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads (thread_id, pub_date) VALUES (?, ?)",
            (thread_id, dt.isoformat()),
        )


def get_thread_date(thread_id: int):
    with _connect() as conn:
        row = conn.execute(
            "SELECT pub_date FROM threads WHERE thread_id = ?", (thread_id,)
        ).fetchone()
    return datetime.fromisoformat(row[0]) if row else None


init_db()


def _origin_date(msg: Message):
    if msg.forward_origin and getattr(msg.forward_origin, "date", None):
        return msg.forward_origin.date
    if msg.forward_date:
        return msg.forward_date
    if msg.sender_chat and msg.sender_chat.id == TARGET_CHANNEL_ID:
        return msg.date
    return None


async def track_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if post and post.chat.id == TARGET_CHANNEL_ID:
        logging.info("Channel post saved: %s date=%s", post.message_id, post.date)
        save_post(post.message_id, post.date)


async def track_auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    dt = _origin_date(msg)
    if dt:
        save_thread(msg.message_id, dt)
        logging.info("Thread mapped: %s -> %s", msg.message_id, dt)


def resolve_post_time(msg: Message):
    if msg.reply_to_message:
        dt = _origin_date(msg.reply_to_message)
        if dt:
            if msg.message_thread_id:
                save_thread(msg.message_thread_id, dt)
            return dt

    if msg.message_thread_id:
        return get_thread_date(msg.message_thread_id)

    return None


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or msg.chat.id != TARGET_GROUP_ID:
        return

    user = msg.from_user
    if not user or user.id == context.bot.id or user.is_bot:
        return

    if not is_single_heart(msg.text or ""):
        return

    post_time = resolve_post_time(msg)
    if not post_time:
        logging.info("Heart from %s but post time unknown — taking no action.", user.id)
        return

    post_time_utc = (
        post_time.astimezone(timezone.utc)
        if post_time.tzinfo
        else post_time.replace(tzinfo=timezone.utc)
    )
    msg_date_utc = (
        msg.date.astimezone(timezone.utc)
        if msg.date.tzinfo
        else msg.date.replace(tzinfo=timezone.utc)
    )

    diff_mins = (msg_date_utc - post_time_utc).total_seconds() / 60.0
    if not 0 <= diff_mins <= WINDOW_MINUTES:
        logging.info("diff %.2f outside 0-%d window", diff_mins, WINDOW_MINUTES)
        return

    user_link = f"tg://user?id={user.id}"
    username_str = f"@{user.username}" if user.username else "No username"
    info_text = (
        "🚨 <b>Heart Emoji Auto-Mute Alert</b>\n\n"
        f"• <b>User:</b> <a href=\"{user_link}\">{html.escape(user.first_name or 'user')}</a>\n"
        f"• <b>Username:</b> {html.escape(username_str)}\n"
        f"• <b>User ID:</b> <code>{user.id}</code>\n"
        f"• <b>Sent:</b> {diff_mins:.1f} mins after channel post"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔨 Ban User", callback_data=f"ban_{user.id}"),
                InlineKeyboardButton("🔊 Unmute User", callback_data=f"unmute_{user.id}"),
                InlineKeyboardButton("❌ Keep Muted", callback_data=f"ignore_{user.id}"),
            ],
            [InlineKeyboardButton("👤 Open Profile", url=user_link)],
        ]
    )

    try:
        await context.bot.forward_message(
            chat_id=ADMIN_DM_ID,
            from_chat_id=TARGET_GROUP_ID,
            message_id=msg.message_id,
        )
    except Exception as e:
        logging.error("Failed to forward message: %s", e)

    try:
        await context.bot.send_message(
            chat_id=ADMIN_DM_ID,
            text=info_text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception as e:
        logging.error("Failed to send DM: %s", e)

    try:
        await msg.delete()
    except Exception as e:
        logging.error("Failed to delete message: %s", e)

    try:
        await context.bot.restrict_chat_member(
            chat_id=TARGET_GROUP_ID,
            user_id=user.id,
            permissions=ChatPermissions.no_permissions(),
        )
    except Exception as e:
        logging.error("Failed to mute user: %s", e)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_DM_ID:
        await query.answer("Not authorized.", show_alert=True)
        return
    await query.answer()

    action, _, raw_id = query.data.partition("_")
    try:
        user_id = int(raw_id)
    except ValueError:
        return

    base = query.message.text_html or ""

    if action == "ban":
        try:
            await context.bot.ban_chat_member(chat_id=TARGET_GROUP_ID, user_id=user_id)
            status = f"✅ <b>User {user_id} has been BANNED.</b>"
        except Exception as e:
            status = f"❌ <b>Failed to ban:</b> {html.escape(str(e))}"
    elif action == "unmute":
        try:
            await context.bot.restrict_chat_member(
                chat_id=TARGET_GROUP_ID,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            status = f"🔊 <b>User {user_id} has been UNMUTED.</b>"
        except Exception as e:
            status = f"❌ <b>Failed to unmute:</b> {html.escape(str(e))}"
    elif action == "ignore":
        status = "ℹ️ <b>Ignored. User remains muted.</b>"
    else:
        return

    await query.edit_message_text(text=f"{base}\n\n{status}", parse_mode="HTML")


async def check_bot_permissions(app):
    bot = app.bot
    try:
        member = await bot.get_chat_member(TARGET_GROUP_ID, bot.id)
        if member.status not in ("administrator", "creator"):
            await bot.send_message(
                chat_id=ADMIN_DM_ID, text="⚠️ Bot is NOT an admin in the target group!"
            )
        elif not getattr(member, "can_delete_messages", False) or not getattr(
            member, "can_restrict_members", False
        ):
            await bot.send_message(
                chat_id=ADMIN_DM_ID, text="⚠️ Bot lacks required admin permissions."
            )
    except Exception as e:
        logging.error("Error checking group permissions: %s", e)

    try:
        cmember = await bot.get_chat_member(TARGET_CHANNEL_ID, bot.id)
        if cmember.status not in ("administrator", "creator"):
            await bot.send_message(
                chat_id=ADMIN_DM_ID, text="⚠️ Bot is NOT an admin in the channel!"
            )
    except Exception as e:
        logging.error("Error checking channel permissions: %s", e)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id == ADMIN_DM_ID:
        await update.effective_message.reply_text(
            f"👋 Bot is active and monitoring (Window: {WINDOW_MINUTES} mins)."
        )


async def post_init(app):
    await check_bot_permissions(app)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, track_channel_post))
    app.add_handler(
        MessageHandler(
            filters.Chat(TARGET_GROUP_ID) & filters.IS_AUTOMATIC_FORWARD,
            track_auto_forward,
        )
    )
    app.add_handler(
        MessageHandler(filters.Chat(TARGET_GROUP_ID) & filters.TEXT, handle_group_message)
    )
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
