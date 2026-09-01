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
WINDOW_MINUTES = int(os.getenv("WINDOW_MINUTES", "30"))
DB_PATH = os.path.expanduser(os.getenv("DB_PATH", "~/antinsfwbot/posts.db"))

# --------------------------------------------------------------------------
# Emoji matching
# --------------------------------------------------------------------------
# Each entry is a whole emoji, not a bag of code points.
HEART_EMOJIS_RAW = (
    "🩷", "❤️", "🧡", "💛", "💚", "🩵", "💙", "💜", "🖤", "🩶", "🤍", "🤎",
    "❤️‍🔥", "❤️‍🩹", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "🫦", "👄",
)

# Invisible characters that change the code point count without changing what
# the user sees: VS15/VS16, zero-width space/joiner-adjacent chars, BOM.
_INVISIBLE = dict.fromkeys(map(ord, "\ufe0e\ufe0f\u200b\u200c\ufeff\u2060"), None)


def _normalize(text: str) -> str:
    return text.strip().translate(_INVISIBLE)


HEART_EMOJIS = frozenset(_normalize(e) for e in HEART_EMOJIS_RAW)


def is_single_heart(text: str) -> bool:
    """True if the message is nothing but one heart or suggestive emoji."""
    if not text:
        return False
    return _normalize(text) in HEART_EMOJIS


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS join_messages (
                user_id INTEGER PRIMARY KEY,
                msg_id INTEGER,
                join_date TEXT
            )
            """
        )


def save_join_message(user_id: int, msg_id: int, dt: datetime):
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO join_messages (user_id, msg_id, join_date) VALUES (?, ?, ?)",
            (user_id, msg_id, dt.isoformat()),
        )


def pop_join_message(user_id: int):
    with _connect() as conn:
        row = conn.execute(
            "SELECT msg_id FROM join_messages WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM join_messages WHERE user_id = ?", (user_id,))
            return row[0]
    return None


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


# --------------------------------------------------------------------------
# Post-time resolution
# --------------------------------------------------------------------------
def _origin_date(msg: Message):
    """Publication date of the channel post a group message belongs to."""
    if msg.sender_chat and msg.sender_chat.id == TARGET_CHANNEL_ID:
        return msg.date
    if msg.forward_origin and getattr(msg.forward_origin, "chat", None) and msg.forward_origin.chat.id == TARGET_CHANNEL_ID:
        return msg.forward_origin.date
    if msg.is_automatic_forward:
        return msg.forward_origin.date if (msg.forward_origin and getattr(msg.forward_origin, "date", None)) else msg.date
    return None


async def track_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if post and post.chat.id == TARGET_CHANNEL_ID:
        logging.info("Channel post saved: %s date=%s", post.message_id, post.date)
        save_post(post.message_id, post.date)


async def track_auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record the thread root when Telegram copies a channel post into the group."""
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
        t_date = get_thread_date(msg.message_thread_id)
        if t_date:
            return t_date

    # Fallback to latest tracked target channel post date
    with _connect() as conn:
        row = conn.execute("SELECT pub_date FROM posts ORDER BY datetime(pub_date) DESC LIMIT 1").fetchone()
    if row:
        return datetime.fromisoformat(row[0])

    return None


# --------------------------------------------------------------------------
# Main handler
# --------------------------------------------------------------------------
async def track_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.chat.id == TARGET_GROUP_ID and msg.new_chat_members:
        for member in msg.new_chat_members:
            save_join_message(member.id, msg.message_id, msg.date)
            logging.info("Tracked join message %s for user %s", msg.message_id, member.id)


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
        logging.info("No post time found for message %s, skipping", msg.message_id)
        return

    msg_date_utc = msg.date.astimezone(timezone.utc)
    post_time_utc = post_time.astimezone(timezone.utc)
    diff_mins = (msg_date_utc - post_time_utc).total_seconds() / 60.0

    logging.info(
        "Heart emoji detected! diff_mins=%.2f (msg=%s, post=%s)",
        diff_mins,
        msg_date_utc,
        post_time_utc,
    )

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
                InlineKeyboardButton("🚷 Ban Group", callback_data=f"ban_confirm_{user.id}"),
                InlineKeyboardButton("🚫 Ban Channel", callback_data=f"banchannel_confirm_{user.id}"),
            ],
            [
                InlineKeyboardButton("🔨 Ban Both", callback_data=f"banboth_confirm_{user.id}"),
            ],
            [
                InlineKeyboardButton("🔊 Unmute", callback_data=f"unmute_confirm_{user.id}"),
                InlineKeyboardButton("❌ Keep Muted", callback_data=f"ignore_{user.id}"),
            ],
            [InlineKeyboardButton("👤 Open Profile", url=user_link)],
        ]
    )

    # Forward before deleting — the other order loses the evidence.
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

    data = query.data
    base = query.message.text_html or ""

    if data == "retry_perm_check":
        issues = await check_bot_permissions(context.application, from_retry=True)
        if not issues:
            status_text = "✅ <b>Success: All required bot permissions are now granted!</b>"
            await query.edit_message_text(text=f"{base}\n\n{status_text}", parse_mode="HTML")
        else:
            remaining = "<br>• ".join(issues)
            retry_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Retry Permission Check", callback_data="retry_perm_check")]])
            status_text = f"⚠️ <b>Permissions re-checked but issues remain:</b>\n• {remaining}"
            await query.edit_message_text(text=f"{base}\n\n{status_text}", parse_mode="HTML", reply_markup=retry_kb)
        return

    # Confirmation Prompts
    if data.startswith("banboth_confirm_"):
        uid = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES, Ban from BOTH", callback_data=f"banboth_do_{uid}")],
            [InlineKeyboardButton("Cancel", callback_data=f"reset_{uid}")],
        ])
        await query.edit_message_text(
            text=f"{base}\n\n<b>Are you sure you want to BAN user {uid} from BOTH channel and group?</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    if data.startswith("banchannel_confirm_"):
        uid = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES, Ban from Channel", callback_data=f"banchannel_do_{uid}")],
            [InlineKeyboardButton("Cancel", callback_data=f"reset_{uid}")],
        ])
        await query.edit_message_text(
            text=f"{base}\n\n<b>Are you sure you want to BAN user {uid} from Channel?</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    if data.startswith("ban_confirm_"):
        uid = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES, Ban from Group", callback_data=f"ban_do_{uid}")],
            [InlineKeyboardButton("Cancel", callback_data=f"reset_{uid}")],
        ])
        await query.edit_message_text(
            text=f"{base}\n\n<b>Are you sure you want to BAN user {uid} from Group?</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    if data.startswith("unmute_confirm_"):
        uid = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES, Unmute User", callback_data=f"unmute_do_{uid}")],
            [InlineKeyboardButton("Cancel", callback_data=f"reset_{uid}")],
        ])
        await query.edit_message_text(
            text=f"{base}\n\n<b>Are you sure you want to UNMUTE user {uid}?</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    if data.startswith("reset_"):
        uid = data.split("_")[1]
        user_link = f"tg://user?id={uid}"
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚷 Ban Group", callback_data=f"ban_confirm_{uid}"),
                InlineKeyboardButton("🚫 Ban Channel", callback_data=f"banchannel_confirm_{uid}"),
            ],
            [
                InlineKeyboardButton("🔨 Ban Both", callback_data=f"banboth_confirm_{uid}"),
            ],
            [
                InlineKeyboardButton("🔊 Unmute", callback_data=f"unmute_confirm_{uid}"),
                InlineKeyboardButton("❌ Keep Muted", callback_data=f"ignore_{uid}"),
            ],
            [InlineKeyboardButton("👤 Open Profile", url=user_link)],
        ])
        clean_text = base.split("\n\n<b>Are you sure")[0]
        await query.edit_message_text(text=clean_text, parse_mode="HTML", reply_markup=kb)
        return

    # Action Execution
    if data.startswith("banboth_do_"):
        user_id = int(data.split("_")[2])
        g_res, c_res = "ok", "ok"
        try:
            await context.bot.ban_chat_member(chat_id=TARGET_GROUP_ID, user_id=user_id)
            join_msg_id = pop_join_message(user_id)
            if join_msg_id:
                try:
                    await context.bot.delete_message(chat_id=TARGET_GROUP_ID, message_id=join_msg_id)
                except Exception:
                    pass
        except Exception as e:
            g_res = str(e)
        try:
            await context.bot.ban_chat_member(chat_id=TARGET_CHANNEL_ID, user_id=user_id)
        except Exception as e:
            c_res = str(e)

        if g_res == "ok" and c_res == "ok":
            status = f"✅ <b>User {user_id} BANNED from BOTH channel & group.</b>"
        else:
            status = f"⚠️ <b>Ban Both result:</b> Group ({g_res}), Channel ({c_res})"

    elif data.startswith("banchannel_do_"):
        user_id = int(data.split("_")[2])
        try:
            await context.bot.ban_chat_member(chat_id=TARGET_CHANNEL_ID, user_id=user_id)
            status = f"🚫 <b>User {user_id} BANNED from CHANNEL.</b>"
        except Exception as e:
            status = f"❌ <b>Failed channel ban:</b> {html.escape(str(e))}"

    elif data.startswith("ban_do_"):
        user_id = int(data.split("_")[2])
        try:
            await context.bot.ban_chat_member(chat_id=TARGET_GROUP_ID, user_id=user_id)
            join_msg_id = pop_join_message(user_id)
            if join_msg_id:
                try:
                    await context.bot.delete_message(chat_id=TARGET_GROUP_ID, message_id=join_msg_id)
                except Exception:
                    pass
            status = f"🚷 <b>User {user_id} BANNED from GROUP.</b>"
        except Exception as e:
            status = f"❌ <b>Failed group ban:</b> {html.escape(str(e))}"

    elif data.startswith("unmute_do_"):
        user_id = int(data.split("_")[2])
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
            status = f"🔊 <b>User {user_id} UNMUTED.</b>"
        except Exception as e:
            status = f"❌ <b>Failed to unmute:</b> {html.escape(str(e))}"

    elif data.startswith("ignore_"):
        status = "ℹ️ <b>Ignored. User remains muted.</b>"
    else:
        return

    clean_text = base.split("\n\n⚠️")[0]
    await query.edit_message_text(text=f"{clean_text}\n\n{status}", parse_mode="HTML")


async def check_bot_permissions(app, from_retry=False):
    bot = app.bot
    retry_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Retry Permission Check", callback_data="retry_perm_check")]])
    issues = []
    
    try:
        member = await bot.get_chat_member(TARGET_GROUP_ID, bot.id)
        if member.status not in ("administrator", "creator"):
            issues.append("Bot is NOT an admin in the target group!")
        elif not getattr(member, "can_delete_messages", False) or not getattr(
            member, "can_restrict_members", False
        ):
            issues.append("Bot lacks `can_delete_messages` or `can_restrict_members` admin permissions in group.")
    except Exception as e:
        logging.error("Error checking group permissions: %s", e)
        issues.append(f"Error checking group permissions: {e}")

    try:
        cmember = await bot.get_chat_member(TARGET_CHANNEL_ID, bot.id)
        if cmember.status not in ("administrator", "creator"):
            issues.append("Bot is NOT an admin in the target channel!")
        elif not getattr(cmember, "can_restrict_members", False) and not getattr(cmember, "can_post_messages", False):
            issues.append("Bot is channel admin but lacks permissions to restrict users in channel.")
    except Exception as e:
        logging.error("Error checking channel permissions: %s", e)
        issues.append(f"Error checking channel permissions: {e}")

    if not from_retry:
        for issue in issues:
            await bot.send_message(
                chat_id=ADMIN_DM_ID, text=f"⚠️ <b>Warning:</b> {issue}", parse_mode="HTML", reply_markup=retry_kb
            )
    return issues


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id == ADMIN_DM_ID:
        await update.effective_message.reply_text("👋 Bot is active and monitoring.")


async def post_init(app):
    await check_bot_permissions(app)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, track_channel_post))
    # Must be registered before the general group handler: within one handler
    # group, only the first matching handler runs.
    app.add_handler(
        MessageHandler(
            filters.Chat(TARGET_GROUP_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            track_chat_members,
        )
    )
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
