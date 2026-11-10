"""Tests use a fake documented SDK surface; no TLS or public connection."""
import os
import sys
import types
import unittest
from unittest.mock import patch

from bubbabot.bot_profile import BotProfile
from bubbabot.official_sdk_adapter import wire_mode1_bot
from bubbabot.official_sdk_runner import build_bot
from bubbabot.sdk_bridge import SDKBridge


class FakeBot:
    room = ""
    def __init__(self):
        self.messages = []
        self.handler = None

    def on_message(self, fn):
        self.handler = fn
        return fn

    def say(self, message):
        self.messages.append(message)


class SDKAdapterTests(unittest.TestCase):
    def test_approved_room_replies_via_sdk_say(self):
        sdk = FakeBot()
        wire_mode1_bot(sdk, SDKBridge(
            BotProfile(name="Bubba", site="bubba", room="bubba"),
            cooldown_seconds=0
        ))
        sdk.room = "bubba"
        sdk.handler("Dave", "DavesBBS", "Hey @Bubba")
        self.assertEqual(len(sdk.messages), 1)
        self.assertIn("Dave", sdk.messages[0])

    def test_does_not_send_before_auth_or_in_lobby(self):
        sdk = FakeBot()
        wire_mode1_bot(sdk)
        sdk.handler("Dave", "DavesBBS", "Hey @Bubba")
        sdk.room = "lobby"
        sdk.handler("Dave", "DavesBBS", "Hey @Bubba")
        sdk.room = "other"
        sdk.handler("Dave", "DavesBBS", "Hey @Bubba")
        self.assertEqual(sdk.messages, [])

    def test_rejects_wrong_configured_room(self):
        sdk = FakeBot()
        with self.assertRaises(ValueError):
            wire_mode1_bot(sdk, expected_room="lobby")
        with self.assertRaises(ValueError):
            wire_mode1_bot(sdk, SDKBridge(BotProfile(room="other")))

    def test_ignores_unaddressed_messages(self):
        sdk = FakeBot()
        wire_mode1_bot(sdk)
        sdk.room = "bubba"
        sdk.handler("Dave", "DavesBBS", "Good morning everyone")
        self.assertEqual(sdk.messages, [])

    def test_runner_fails_without_credentials_before_sdk_import(self):
        with patch.dict(os.environ, {
            "CONNECTOR_TOKEN": "", "CONNECTOR_HOST": "",
            "BOT_SLUG": "", "BOT_ROOM": "bubba"
        }):
            with self.assertRaises(ValueError):
                build_bot()

    def test_runner_uses_official_sdk_with_verified_tls(self):
        created = []
        class FakeMRCBot(FakeBot):
            def __init__(self, **kwargs):
                super().__init__()
                created.append(kwargs)
        module = types.ModuleType("mrc_connector")
        module.MRCBot = FakeMRCBot
        with patch.dict(sys.modules, {"mrc_connector": module}):
            with patch.dict(os.environ, {
                "CONNECTOR_TOKEN": "fake-test-only",
                "CONNECTOR_HOST": "connector.example.test",
                "BOT_SLUG": "bubba",
                "BOT_ROOM": "bubba",
                "CONNECTOR_PORT": "5010"
            }):
                bot = build_bot()
        self.assertEqual(created[0]["verify_tls"], True)
        self.assertEqual(created[0]["port"], 5010)
        self.assertFalse(created[0]["debug"])
        self.assertEqual(bot.display_name, "Bubba")


if __name__ == "__main__":
    unittest.main()
