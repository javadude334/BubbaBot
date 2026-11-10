"""Offline personality tests."""
import unittest

from bubbabot.personality import Personality


class PersonalityTests(unittest.TestCase):
    def setUp(self):
        self.bubba = Personality()

    def test_help(self):
        self.assertIn(".joke", self.bubba.respond("Dave", ".help"))

    def test_case_insensitive_commands(self):
        self.assertIn("Dave's BBS", self.bubba.respond("Dave", " .ABOUT "))

    def test_status(self):
        self.assertIn("AI chat may be unavailable", self.bubba.respond("Dave", ".status"))

    def test_joke_is_deterministic(self):
        self.assertEqual(self.bubba.respond("Dave", ".joke"), self.bubba.respond("Dave", ".joke"))

    def test_unknown_input_does_not_invent_ai_reply(self):
        self.assertIsNone(self.bubba.respond("Dave", "Bubba, how are you?"))

    def test_invalid_input(self):
        self.assertIsNone(self.bubba.respond(None, ".help"))


if __name__ == "__main__":
    unittest.main()
