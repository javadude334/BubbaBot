"""Offline tests for cached verified college-football facts."""
import io
import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from bubbabot import sports


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class SportsTests(unittest.TestCase):
    def setUp(self):
        sports._cache.clear()
        self.now = datetime(2026, 11, 11, 12, tzinfo=ZoneInfo("America/Chicago"))

    def test_football_question_detected_without_triggering_on_smalltalk(self):
        self.assertEqual(sports.mentioned_teams("Who's Alabama playing this weekend?"), ["alabama"])
        self.assertEqual(sports.mentioned_teams("Troy and South Alabama game?"), ["troy", "south alabama"])
        self.assertEqual(sports.mentioned_teams("I love Troy"), [])
        self.assertEqual(sports.mentioned_teams("What about your truck?"), [])

    def test_schedule_is_verified_and_cached(self):
        calls = []
        payload = {"events": [{"date": "2026-11-14T19:00:00Z",
            "competitions": [{"competitors": [
                {"team": {"displayName": "Troy Trojans"}},
                {"team": {"displayName": "South Alabama Jaguars"}}]}],
            "status": {"type": {"state": "pre"}}}]}
        def transport(request, timeout):
            calls.append(request if isinstance(request, str) else request.full_url)
            return Response(json.dumps(payload).encode())
        msg = "Who is Troy playing this weekend?"
        answer = sports.sports_context(msg, now=self.now, transport=transport, clock=lambda: 100)
        self.assertIn("South Alabama Jaguars", answer)
        self.assertIn("(pre)", answer)
        self.assertNotIn("score Troy", answer)
        sports.sports_context(msg, now=self.now, transport=transport, clock=lambda: 101)
        self.assertEqual(len(calls), 1)

    def test_network_failure_never_invents_opponent(self):
        def offline(request, timeout):
            raise OSError("offline")
        result = sports.sports_context("Alabama game this weekend?", now=self.now, transport=offline)
        self.assertIn("No verified game found", result)
        self.assertNotIn("Troy Trojans", result)

    def test_null_status_upcoming_weekend_and_later_opponent(self):
        payload = {"events": [
            {"date": "2026-11-14T19:00Z", "status": None,
             "competitions": [{"competitors": [
                 {"team": {"displayName": "Troy Trojans"}},
                 {"team": {"displayName": "South Alabama Jaguars"}}]}]},
            {"date": "2026-11-28T20:00Z", "status": None,
             "competitions": [{"competitors": [
                 {"team": {"displayName": "Troy Trojans"}},
                 {"team": {"displayName": "Arkansas State Red Wolves"}}]}]}
        ]}
        def transport(request, timeout):
            return Response(json.dumps(payload).encode())
        result = sports.sports_context("Who is Troy playing this weekend?",
                                       now=self.now, transport=transport)
        self.assertIn("South Alabama Jaguars", result)
        self.assertNotIn("Arkansas State", result)
        self.assertIn("(pre)", result)

    def test_non_sports_chat_avoids_lookup(self):
        self.assertEqual(sports.sports_context("I love Troy!", now=self.now), "")


if __name__ == "__main__":
    unittest.main()
