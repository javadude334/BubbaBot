import unittest
from datetime import date
from bubbabot.holidays import easter, holidays, holiday_context


class HolidayTests(unittest.TestCase):
    def test_easter(self):
        self.assertEqual(easter(2026), date(2026, 4, 5))
        self.assertEqual(easter(2027), date(2027, 3, 28))

    def test_thanksgiving(self):
        self.assertIn("Thanksgiving", holidays(2026)[date(2026, 11, 26)])

    def test_christmas_countdown(self):
        context = holiday_context(date(2026, 12, 24))
        self.assertIn("Christmas Day in 1 day(s)", context)

    def test_new_year_rollover(self):
        context = holiday_context(date(2026, 12, 31))
        self.assertIn("New Year's Eve", context)


if __name__ == "__main__":
    unittest.main()
