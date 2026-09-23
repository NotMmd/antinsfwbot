import os
import tempfile
import unittest

from db import Database
from settings import (
    SETTING_LABELS,
    build_keyboard,
    get_actionable_verdict,
    is_admin_allowed,
    toggle_setting,
)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.temp_dir.name, "bot.sqlite3"))

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_toggle_persists_and_returns_new_value(self):
        self.assertIn("enabled", SETTING_LABELS)
        self.assertFalse(toggle_setting(self.db, "enabled"))
        self.assertFalse(self.db.get_setting("enabled", True))
        self.assertTrue(toggle_setting(self.db, "enabled"))

    def test_unknown_setting_is_rejected(self):
        with self.assertRaises(ValueError):
            toggle_setting(self.db, "arbitrary")

    def test_engine_toggle_alternates_between_jev_and_laya(self):
        self.assertEqual(toggle_setting(self.db, "system_one_engine"), "laya")
        self.assertEqual(toggle_setting(self.db, "system_one_engine"), "jev")

    def test_settings_access_requires_an_explicit_admin_id(self):
        self.assertFalse(is_admin_allowed((), 77))
        self.assertTrue(is_admin_allowed((77, 88), 77))
        self.assertFalse(is_admin_allowed((77, 88), 99))

    def test_cached_verdict_is_inactive_while_classification_is_disabled(self):
        self.db.cache_verdict(-100, 9, {"verdict": "nsfw"})
        self.db.set_setting("enabled", False)
        self.assertIsNone(get_actionable_verdict(self.db, -100, 9))

    def test_keyboard_reflects_stored_state_and_scopes_callback(self):
        keyboard = build_keyboard(self.db, requester_id=77)
        first_button = keyboard.inline_keyboard[0][0]
        self.assertIn("ON", first_button.text)
        self.assertEqual(first_button.callback_data, "setting:toggle:enabled:77")
        self.assertIn("JEV", keyboard.inline_keyboard[2][0].text)


if __name__ == "__main__":
    unittest.main()
