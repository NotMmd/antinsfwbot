import os
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

_test_db_dir = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = os.path.join(_test_db_dir.name, "import.sqlite3")
import main

from settings import get_settings, set_setting


class AdminPanelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        main.DB_PATH = os.path.join(self.temp_dir.name, "bot.sqlite3")
        main.TARGET_GROUP_ID = -1001
        main.TARGET_CHANNEL_ID = -2001
        main.ADMIN_IDS = {42}
        main.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    async def test_admin_panel_callback_persists_toggle_and_refreshes_panel(self):
        query = SimpleNamespace(
            from_user=SimpleNamespace(id=42),
            data="settings:toggle:auto_ban",
            message=SimpleNamespace(text_html="⚙️ Moderation settings"),
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(callback_query=query)

        await main.handle_callback(update, SimpleNamespace())

        self.assertTrue(
            get_settings(main.DB_PATH, main.TARGET_GROUP_ID, main.TARGET_CHANNEL_ID)["auto_ban"]
        )
        query.answer.assert_awaited_once()
        query.edit_message_text.assert_awaited_once()
        self.assertIn("Auto-ban: ON", query.edit_message_text.await_args.kwargs["text"])

    async def test_detection_uses_live_delete_notify_and_ban_settings(self):
        for key, value in {
            "auto_ban": True,
            "auto_delete": False,
            "ban_scope": "both",
            "notify_admin": False,
        }.items():
            set_setting(key, value, main.DB_PATH, main.TARGET_GROUP_ID, main.TARGET_CHANNEL_ID)

        now = datetime.now(timezone.utc)
        message = SimpleNamespace(
            chat=SimpleNamespace(id=main.TARGET_GROUP_ID),
            from_user=SimpleNamespace(id=77, username="spammer", first_name="Spam", is_bot=False),
            text="❤️",
            date=now,
            message_id=9,
            delete=AsyncMock(),
        )
        bot = SimpleNamespace(
            id=100,
            ban_chat_member=AsyncMock(),
            restrict_chat_member=AsyncMock(),
            forward_message=AsyncMock(),
            send_message=AsyncMock(),
            delete_message=AsyncMock(),
        )

        with patch.object(main, "resolve_post_time", return_value=now):
            await main.handle_group_message(
                SimpleNamespace(effective_message=message), SimpleNamespace(bot=bot)
            )

        self.assertEqual(
            [call.kwargs["chat_id"] for call in bot.ban_chat_member.await_args_list],
            [main.TARGET_GROUP_ID, main.TARGET_CHANNEL_ID],
        )
        message.delete.assert_not_awaited()
        bot.forward_message.assert_not_awaited()
        bot.send_message.assert_not_awaited()
        bot.restrict_chat_member.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
