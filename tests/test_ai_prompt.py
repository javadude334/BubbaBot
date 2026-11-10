import unittest
from datetime import date
from bubbabot.ai.prompt import build_messages


class PromptTests(unittest.TestCase):
    def test_holiday_and_persona(self):
        messages = build_messages("Howdy", today=date(2026, 12, 25))
        self.assertIn("Christmas Day", messages[0]["content"])
        self.assertIn("Civil War", messages[0]["content"])
        self.assertEqual(messages[-1]["content"], "Howdy")

    def test_bounded_history(self):
        history = [{"role": "user", "content": str(i)} for i in range(20)]
        self.assertEqual(len(build_messages("Hi", history)), 10)


if __name__ == "__main__":
    unittest.main()
