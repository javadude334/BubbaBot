import unittest
from bubbabot.memory_privacy import screen_memory_note


class MemoryPrivacyTests(unittest.TestCase):
    def test_allowlisted_interest(self):
        self.assertEqual(screen_memory_note("Enjoys fishing"), "Enjoys fishing")

    def test_reject_email(self):
        self.assertIsNone(screen_memory_note("Email me at sam@example.com"))

    def test_reject_phone(self):
        self.assertIsNone(screen_memory_note("Call 555-123-4567"))

    def test_reject_name(self):
        self.assertIsNone(screen_memory_note("Sam enjoys fishing"))

    def test_reject_unrecognized_detail(self):
        self.assertIsNone(screen_memory_note("Enjoys fishing with Bob"))

    def test_reject_sensitive(self):
        self.assertIsNone(screen_memory_note("Has a medical diagnosis"))

    def test_reject_non_string(self):
        self.assertIsNone(screen_memory_note(None))


if __name__ == "__main__":
    unittest.main()
