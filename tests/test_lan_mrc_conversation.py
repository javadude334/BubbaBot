"""Tests for private LAN chat conversation activation and expiry."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from bubbabot.lan_mrc_adapter import is_conversation_message, broadcast_fields, encode, complete_reply, current_instructions, unverified_sports_reply


class ConversationTests(unittest.TestCase):
    def test_public_reply_preserves_working_broadcast_and_sender(self):
        fields = broadcast_fields("Howdy, neighbor!")
        self.assertEqual(fields, ("Bubba", "BubbaBot_Ubuntu", "bubba", "", "", "bubba", "|03<|10Bubba|03>|16|07 Howdy, neighbor!"))
        self.assertEqual(
            encode(fields),
            "Bubba~BubbaBot_Ubuntu~bubba~~~bubba~|03<|10Bubba|03>|16|07 Howdy, neighbor!~\n",
        )

    def test_complete_reply_never_cuts_mid_sentence(self):
        self.assertEqual(complete_reply("That's funny. " + "Extra words " * 30), "That's funny.")
        self.assertEqual(complete_reply("Hey there!"), "Hey there!")

    def test_date_and_style_instructions(self):
        instructions = current_instructions(datetime(2026, 11, 10, 20, 0, tzinfo=ZoneInfo("America/Chicago")))
        self.assertIn("Tuesday, November 10, 2026", instructions)
        self.assertIn("Don't end every message with a question", instructions)

    def test_unverified_troy_season_question_avoids_inventing_results(self):
        reply = unverified_sports_reply("Man what's going on with Troy this year?")
        self.assertIn("haven't checked", reply)
        self.assertNotIn("South Alabama", reply)

    def test_battle_for_the_belt_is_rivalry_not_completed_result(self):
        reply = unverified_sports_reply("Troy vs South Alabama game?")
        self.assertIn("Battle for the Belt", reply)
        self.assertIn("ain't checked", reply)

    def test_regular_chat_is_not_intercepted(self):
        self.assertIsNone(unverified_sports_reply("I'm fishing at the river."))
        self.assertIsNone(unverified_sports_reply("Hey Bubba, how's your truck?"))

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
