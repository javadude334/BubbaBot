import json
import tempfile
import unittest
from pathlib import Path

from bubbabot.settings import Settings, load_settings


class SettingsTests(unittest.TestCase):
    def test_defaults_are_loopback_only(self):
        self.assertEqual(Settings().host, "127.0.0.1")

    def test_rejects_public_host(self):
        with self.assertRaises(ValueError):
            Settings(host="mrc.bottomlessabyss.net")

    def test_rejects_unknown_json_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps({"api_key": "nope"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_settings(path)

    def test_custom_bot_identity_and_room(self):
        settings = Settings(bot_name="Bubba", site="BubbaTest", room="#Bubba")
        self.assertEqual(settings.bot_name, "Bubba")
        self.assertEqual(settings.room, "#Bubba")

    def test_rejects_invalid_bot_identity(self):
        with self.assertRaises(ValueError):
            Settings(bot_name="Bad~Bot")
        with self.assertRaises(ValueError):
            Settings(room="bad room")

    def test_reads_valid_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps({"room": "Testing", "port": 5050}), encoding="utf-8")
            self.assertEqual(load_settings(path).room, "Testing")


if __name__ == "__main__":
    unittest.main()
