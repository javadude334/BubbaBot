import unittest

from bubbabot.protocol import Packet, encode_packet, parse_packet
from bubbabot.routing import should_reply


class PacketTests(unittest.TestCase):
    def test_roundtrip(self):
        pkt = Packet("Joe", "Other BBS", "BUBBA", "ALL", "ALL", "BUBBA", "Hey @Bubba!")
        self.assertEqual(parse_packet(encode_packet(pkt)), pkt)

    def test_invalid_packet(self):
        with self.assertRaises(ValueError):
            parse_packet("not~enough~fields")

    def test_reject_field_delimiter(self):
        pkt = Packet("Joe", "Site", "BUBBA", "ALL", "ALL", "BUBBA", "Oops~bad")
        with self.assertRaises(ValueError):
            encode_packet(pkt)

    def test_reply_to_mention(self):
        pkt = Packet("Joe", "Other BBS", "BUBBA", "ALL", "ALL", "BUBBA", "Hey Bubba, help?")
        self.assertTrue(should_reply(pkt, allowed_rooms={"BUBBA"}))

    def test_no_reply_unapproved_room(self):
        pkt = Packet("Joe", "Other BBS", "GENERAL", "ALL", "ALL", "GENERAL", "@Bubba hi")
        self.assertFalse(should_reply(pkt, allowed_rooms={"BUBBA"}))

    def test_no_reply_from_bot(self):
        pkt = Packet("Bubba", "BubbaBot", "BUBBA", "ALL", "ALL", "BUBBA", "@Bubba hi")
        self.assertFalse(should_reply(pkt, allowed_rooms={"BUBBA"}))

    def test_no_reply_other_recipient(self):
        pkt = Packet("Joe", "Other BBS", "BUBBA", "Alice", "Other BBS", "BUBBA", "@Bubba hi")
        self.assertFalse(should_reply(pkt, allowed_rooms={"BUBBA"}))


if __name__ == "__main__":
    unittest.main()
