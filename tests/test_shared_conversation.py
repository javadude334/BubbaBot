"""Offline tests for shared AI routing. No network requests or database access."""
import unittest

from bubbabot.conversation_service import ConversationService
from bubbabot.sdk_bridge import IncomingChat, SDKBridge
from bubbabot.bot_profile import BotProfile


class SharedConversationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.now = [100.0]

        def fake_ai(messages, **kwargs):
            self.calls.append(messages)
            return "Howdy from AI.", {}

        self.conversation = ConversationService(
            api_key="test-only", clock=lambda: self.now[0], responder=fake_ai,
        )

    def test_sdk_uses_ai_not_offline_greeting(self):
        bridge = SDKBridge(BotProfile(room="bubba"), conversation=self.conversation)
        result = bridge.handle(IncomingChat("Dave", "DavesBBS", "bubba", "@bubba hey"))
        self.assertEqual(result.text, "Howdy from AI.")
        self.assertNotIn("offline test mode", result.text)

    def test_followup_and_separate_users(self):
        self.assertEqual(self.conversation.handle("Dave", "DavesBBS", "bubba", "@bubba hey"), "Howdy from AI.")
        self.now[0] += 6
        self.assertEqual(self.conversation.handle("Dave", "DavesBBS", "bubba", "and then?"), "Howdy from AI.")
        self.assertEqual(len(self.calls[-1]), 3)
        self.assertIsNone(self.conversation.handle("Other", "OtherBBS", "bubba", "and then?"))

    def test_room_and_self_exclusion(self):
        self.assertIsNone(self.conversation.handle("Dave", "DavesBBS", "lobby", "@bubba hey"))
        self.assertIsNone(self.conversation.handle("Bubba", "DavesBBS", "bubba", "@bubba hey"))
        self.assertEqual(self.calls, [])

    def test_failed_ai_does_not_send_offline_fallback(self):
        def broken(*args, **kwargs):
            raise RuntimeError("test failure")
        self.conversation.responder = broken
        self.assertIsNone(self.conversation.handle("Dave", "DavesBBS", "bubba", "@bubba hey"))


if __name__ == "__main__":
    unittest.main()
