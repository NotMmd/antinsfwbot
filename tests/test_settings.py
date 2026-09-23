import os
import tempfile
import unittest
from unittest.mock import patch

from settings import DEFAULT_SETTINGS, get_settings, set_setting


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "settings.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_settings_use_environment_values_when_no_database_override_exists(self):
        with patch.dict(os.environ, {
            "AUTO_BAN": "true",
            "AUTO_DELETE": "false",
            "BAN_SCOPE": "both",
            "NOTIFY_ADMIN": "0",
        }, clear=True):
            settings = get_settings(self.db_path, -1001, -2001)

        self.assertEqual(settings, {
            "auto_ban": True,
            "auto_delete": False,
            "ban_scope": "both",
            "notify_admin": False,
        })

    def test_database_override_persists_and_is_scoped_to_group_channel_pair(self):
        set_setting("auto_ban", True, self.db_path, -1001, -2001)

        self.assertTrue(get_settings(self.db_path, -1001, -2001)["auto_ban"])
        self.assertEqual(
            get_settings(self.db_path, -1002, -2001), DEFAULT_SETTINGS
        )

    def test_invalid_settings_are_rejected(self):
        with self.assertRaises(ValueError):
            set_setting("ban_scope", "users", self.db_path, -1001, -2001)

        with self.assertRaises(KeyError):
            set_setting("unknown", True, self.db_path, -1001, -2001)


if __name__ == "__main__":
    unittest.main()
