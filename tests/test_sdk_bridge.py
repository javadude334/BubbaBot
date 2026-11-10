import unittest

from bubbabot.bot_profile import BotProfile
from bubbabot.sdk_bridge import IncomingChat, OutgoingChat, SDKBridge


class SDKBridgeTests(unittest.TestCase):
    def test_replies_to_mention_in_dedicated_room(self):
        bridge = SDKBridge(cooldown_seconds=0)
        reply = bridge.handle(IncomingChat("Dave", "DavesBBS", "#Bubba", "Hey @Bubba"))
        self.assertIsInstance(reply, OutgoingChat)
        self.assertEqual(reply.room, "Bubba")
        self.assertIn("Dave", reply.text)

    def test_lobby_is_never_allowed(self):
        with self.assertRaises(ValueError):
            SDKBridge(BotProfile(room="#lobby"))
        bridge = SDKBridge(cooldown_seconds=0)
        self.assertIsNone(bridge.handle(
            IncomingChat("Dave", "DavesBBS", "#lobby", "Hey @Bubba")))

    def test_ignores_other_rooms_and_unaddressed_messages(self):
        bridge = SDKBridge(cooldown_seconds=0)
        self.assertIsNone(bridge.handle(
            IncomingChat("Dave", "DavesBBS", "#other", "Hey @Bubba")))
        self.assertIsNone(bridge.handle(
            IncomingChat("Dave", "DavesBBS", "#Bubba", "Hello everyone")))

    def test_ignores_self(self):
        bridge = SDKBridge(cooldown_seconds=0)
        self.assertIsNone(bridge.handle(
            IncomingChat("Bubba", "BubbaBot", "#Bubba", "Hey @Bubba")))

    def test_rejects_unknown_event_type(self):
        with self.assertRaises(TypeError):
            SDKBridge().handle({"room": "Bubba"})


if __name__ == "__main__":
    unittest.main()
