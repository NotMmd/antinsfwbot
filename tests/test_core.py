import os
import tempfile
import unittest
import asyncio
from unittest.mock import patch

from config import Config
from classifier import ClassifierRouter
from db import Database
from jev import JevClassifier, build_payload, collect_payload


class ConfigTests(unittest.TestCase):
    def test_loads_telegram_credentials_and_optional_paths(self):
        with patch.dict(os.environ, {
            "API_ID": "123", "API_HASH": "hash", "BOT_TOKEN": "token",
            "DATABASE_PATH": "/tmp/bot.sqlite3", "JEV_API_URL": "https://jev.test/classify",
        }, clear=True):
            config = Config.from_env()
        self.assertEqual((config.api_id, config.api_hash, config.bot_token), (123, "hash", "token"))
        self.assertEqual(config.database_path, "/tmp/bot.sqlite3")
        self.assertEqual(config.jev_api_url, "https://jev.test/classify")

    def test_selects_configured_system_one_engine(self):
        with patch.dict(os.environ, {
            "API_ID": "123", "API_HASH": "hash", "BOT_TOKEN": "token",
            "SYSTEM_ONE_ENGINE": "laya", "LAYA_API_URL": "https://laya.test/classify",
        }, clear=True):
            config = Config.from_env()
        self.assertEqual(config.system_one_engine, "laya")
        self.assertEqual(config.laya_api_url, "https://laya.test/classify")


class JevPayloadTests(unittest.TestCase):
    def test_payload_includes_comment_profile_personal_channel_and_preview(self):
        payload = build_payload(
            comment_text="triggering comment",
            user={"first_name": "Ada", "last_name": "Lovelace", "username": "ada", "bio": "about"},
            personal_channel={"title": "Ada's channel", "username": "ada_posts"},
            preview_text="pinned post preview",
        )
        self.assertEqual(payload, {
            "comment": "triggering comment",
            "user": {"first_name": "Ada", "last_name": "Lovelace", "username": "ada", "bio": "about"},
            "personal_channel": {"title": "Ada's channel", "username": "ada_posts"},
            "preview_text": "pinned post preview",
        })

    def test_classifier_sends_payload_to_configured_transport(self):
        calls = []

        def transport(url, payload, api_key):
            calls.append((url, payload, api_key))
            return {"verdict": "safe", "confidence": 0.99}

        classifier = JevClassifier("https://jev.test/classify", "secret", transport)
        payload = build_payload("hello", {}, None, "post")
        result = asyncio.run(classifier.classify(payload))
        self.assertEqual(result["verdict"], "safe")
        self.assertEqual(calls, [("https://jev.test/classify", payload, "secret")])

    def test_router_dispatches_to_selected_engine(self):
        calls = []

        class Stub:
            async def classify(self, payload):
                calls.append(payload["engine"])
                return {"verdict": payload["engine"]}

        router = ClassifierRouter({"jev": Stub(), "laya": Stub()})
        result = asyncio.run(router.classify({"engine": "laya"}, "laya"))
        self.assertEqual(result["verdict"], "laya")
        self.assertEqual(calls, ["laya"])

    def test_collect_payload_reads_bio_and_reply_preview(self):
        class Client:
            async def get_chat(self, user_id):
                return type("FullUser", (), {"bio": "profile bio"})()

        user = type("User", (), {
            "id": 44, "first_name": "Ada", "last_name": "Lovelace", "username": "ada",
        })()
        reply = type("Reply", (), {"id": 8, "text": "channel preview", "caption": None})()
        message = type("Message", (), {
            "from_user": user, "reply_to_message": reply, "text": "comment text",
            "caption": None, "chat": type("Chat", (), {"id": -100})(),
        })()
        payload = asyncio.run(collect_payload(Client(), message, None))
        self.assertEqual(payload["comment"], "comment text")
        self.assertEqual(payload["user"]["bio"], "profile bio")
        self.assertEqual(payload["preview_text"], "channel preview")

    def test_collect_payload_resolves_personal_channel_id_and_tracked_forward(self):
        class Client:
            async def get_chat(self, chat_id):
                if chat_id == 44:
                    return type("FullUser", (), {"bio": "", "personal_channel_id": -200})()
                return type("Channel", (), {"title": "Personal", "username": "personal"})()

        class DatabaseStub:
            def get_post(self, chat_id, message_id):
                return "saved channel post" if (chat_id, message_id) == (-300, 9) else None

        user = type("User", (), {
            "id": 44, "first_name": "Ada", "last_name": "", "username": "ada",
        })()
        forward_chat = type("ForwardChat", (), {"id": -300})()
        reply = type("Reply", (), {
            "id": 8, "text": None, "caption": None,
            "forward_from_chat": forward_chat, "forward_from_message_id": 9,
        })()
        message = type("Message", (), {
            "from_user": user, "reply_to_message": reply, "text": "comment",
            "caption": None, "chat": type("Chat", (), {"id": -100})(),
        })()
        payload = asyncio.run(collect_payload(Client(), message, DatabaseStub()))
        self.assertEqual(payload["personal_channel"], {"title": "Personal", "username": "personal"})
        self.assertEqual(payload["preview_text"], "saved channel post")

    def test_collect_payload_falls_back_to_chat_pinned_message(self):
        class Client:
            async def get_chat(self, chat_id):
                if chat_id == 44:
                    return type("FullUser", (), {"bio": ""})()
                pinned = type("Pinned", (), {"text": "pinned context", "caption": None})()
                return type("ChatInfo", (), {"pinned_message": pinned})()

        user = type("User", (), {
            "id": 44, "first_name": "Ada", "last_name": "", "username": "ada",
        })()
        message = type("Message", (), {
            "from_user": user, "reply_to_message": None, "text": "comment",
            "caption": None, "chat": type("Chat", (), {"id": -100})(),
        })()
        payload = asyncio.run(collect_payload(Client(), message, None))
        self.assertEqual(payload["preview_text"], "pinned context")


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.temp_dir.name, "bot.sqlite3"))

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_settings_round_trip_with_defaults(self):
        self.assertTrue(self.db.get_setting("enabled", True))
        self.assertFalse(self.db.get_setting("delete_nsfw", False))
        self.db.set_setting("enabled", False)
        self.assertFalse(self.db.get_setting("enabled", True))

    def test_tracks_posts_and_caches_verdicts(self):
        self.db.track_post(-1001, 22, "post preview")
        self.assertEqual(self.db.get_post(-1001, 22), "post preview")
        self.assertIsNone(self.db.get_verdict(-1001, 23))
        self.db.cache_verdict(-1001, 23, {"verdict": "nsfw", "confidence": 0.92})
        self.assertEqual(self.db.get_verdict(-1001, 23), {"verdict": "nsfw", "confidence": 0.92})


if __name__ == "__main__":
    unittest.main()
