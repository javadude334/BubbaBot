"""Offline chat-engine tests. No live MRC or OpenAI connections."""
import unittest

from bubbabot.engine import BubbaEngine
from bubbabot.protocol import Packet


def packet(message="Bubba hello", user="Alice", site="TestBBS", room="lobby"):
    return Packet(user, site, room, "ALL", "", room, message)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        self.engine = BubbaEngine({"lobby"}, clock=lambda: self.now)

    def test_mention_responds(self):
        reply = self.engine.process(packet())
        self.assertEqual(reply.recipient, "Alice")
        self.assertIn("offline test mode", reply.text)

    def test_ignores_unaddressed_and_other_rooms(self):
        self.assertIsNone(self.engine.process(packet("hello everyone")))
        self.assertIsNone(self.engine.process(packet(room="other")))

    def test_ignores_own_messages(self):
        self.assertIsNone(self.engine.process(packet(user="Bubba")))

    def test_cooldown(self):
        self.assertIsNotNone(self.engine.process(packet()))
        self.assertIsNone(self.engine.process(packet()))
        self.now += 30
        self.assertIsNotNone(self.engine.process(packet()))

    def test_global_hourly_limit(self):
        engine = BubbaEngine({"lobby"}, cooldown_seconds=0,
                             max_replies_per_hour=1, clock=lambda: self.now)
        self.assertIsNotNone(engine.process(packet()))
        self.assertIsNone(engine.process(packet(user="Bob")))
        self.now += 3600
        self.assertIsNotNone(engine.process(packet(user="Bob")))

    def test_rejects_oversized_input(self):
        self.assertIsNone(self.engine.process(packet("Bubba " + "x" * 500)))


if __name__ == "__main__":
    unittest.main()
