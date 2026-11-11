"""Tests for private LAN chat conversation activation and expiry."""
import unittest

from bubbabot.lan_mrc_adapter import is_conversation_message


class ConversationTests(unittest.TestCase):
    def test_explicit_mention_starts_conversation(self):
        self.assertTrue(is_conversation_message("@Bubba howdy", 0, 100))
        self.assertTrue(is_conversation_message("Bubba, howdy", 0, 100))

    def test_followup_during_active_session(self):
        self.assertTrue(is_conversation_message("What about tomorrow?", 700, 101))

    def test_unaddressed_message_without_session_is_ignored(self):
        self.assertFalse(is_conversation_message("Hey everyone", 0, 100))

    def test_expired_session_requires_new_mention(self):
        self.assertFalse(is_conversation_message("Still there?", 700, 700))
        self.assertTrue(is_conversation_message("@Bubba still there?", 700, 700))


if __name__ == "__main__":
    unittest.main()
