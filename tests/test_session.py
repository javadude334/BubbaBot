import io
import unittest

from bubbabot.engine import BubbaEngine
from bubbabot.protocol import Packet, encode_packet, parse_packet
from bubbabot.session import OfflineSession


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = OfflineSession(BubbaEngine(
            allowed_rooms={"BubbaRoom"}, cooldown_seconds=0
        ))

    def packet(self, message, room="BubbaRoom", user="Dave"):
        return encode_packet(Packet(user, "DaveBBS", room, "ALL", "", room, message))

    def test_mention_roundtrip(self):
        response = self.session.handle_line(self.packet("Hey @Bubba"))
        self.assertIsNotNone(response)
        decoded = parse_packet(response)
        self.assertEqual(decoded.from_user, "Bubba")
        self.assertEqual(decoded.from_site, "BubbaBot")
        self.assertEqual(decoded.to_room, "BubbaRoom")
        self.assertIn("Howdy, Dave", decoded.message)

    def test_ignores_other_room(self):
        self.assertIsNone(self.session.handle_line(self.packet("@Bubba", "OtherRoom")))

    def test_ignores_malformed_packet(self):
        self.assertIsNone(self.session.handle_line("invalid packet\n"))

    def test_ignores_self_reply(self):
        self.assertIsNone(self.session.handle_line(encode_packet(
            Packet("Bubba", "BubbaBot", "BubbaRoom", "ALL", "", "BubbaRoom", "@Bubba")
        )))

    def test_stream_only_emits_replies(self):
        incoming = io.StringIO(self.packet("hello") + self.packet("@Bubba") + "broken\n")
        outgoing = io.StringIO()
        self.session.run(incoming, outgoing)
        lines = outgoing.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(parse_packet(lines[0]).from_user, "Bubba")


if __name__ == "__main__":
    unittest.main()
