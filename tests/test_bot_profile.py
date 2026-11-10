import unittest

from bubbabot.bot_profile import BotProfile, normalize_room
from bubbabot.room_manager import OfflineRoomManager
from bubbabot.protocol import Packet, encode_packet, parse_packet


class BotProfileTests(unittest.TestCase):
    def test_defaults_and_room_normalization(self):
        p = BotProfile()
        self.assertEqual(p.room, "Bubba")
        self.assertTrue(p.accepts_room("#bubba"))
        self.assertTrue(p.accepts_room("BUBBA"))
        self.assertFalse(p.accepts_room("#lobby"))
        self.assertEqual(normalize_room("#Bubba"), "Bubba")

    def test_rejects_invalid_identity_and_rooms(self):
        for kwargs in ({"name": "Bubba~bad"}, {"site": "Dave's BBS"},
                       {"room": "#"}, {"room": "bad~room"},
                       {"room": "bad\nroom"}, {"room": "bad room"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    BotProfile(**kwargs)

    def test_multiple_users_same_room_and_control_ignored(self):
        manager = OfflineRoomManager(BotProfile())
        inputs = [
            Packet("Dave", "DavesBBS", "Bubba", "ALL", "", "Bubba", "Hey @Bubba"),
            Packet("Alice", "OtherBBS", "bubba", "ALL", "", "bubba", "Hi Bubba"),
            Packet("SERVER", "", "", "ALL", "", "", "PING"),
            Packet("Bob", "ThirdBBS", "lobby", "ALL", "", "lobby", "Hey Bubba"),
            Packet("Bubba", "BubbaBot", "Bubba", "ALL", "", "Bubba", "Hey Bubba"),
        ]
        outputs = [manager.handle_line(encode_packet(p)) for p in inputs]
        replies = [parse_packet(x) for x in outputs if x]
        self.assertEqual(len(replies), 2)
        self.assertEqual([p.from_user for p in replies], ["Bubba", "Bubba"])
        self.assertEqual([p.from_site for p in replies], ["BubbaBot", "BubbaBot"])
        self.assertIn("Dave", replies[0].message)
        self.assertIn("Alice", replies[1].message)

    def test_configurable_identity_and_room(self):
        profile = BotProfile(name="Bubba", site="BubbaTest", room="#TestRoom")
        manager = OfflineRoomManager(profile)
        packet = Packet("Dave", "DavesBBS", "TestRoom", "ALL", "",
                        "TestRoom", "@Bubba status")
        reply = parse_packet(manager.handle_line(encode_packet(packet)))
        self.assertEqual(reply.from_site, "BubbaTest")
        self.assertEqual(reply.from_room, "TestRoom")


if __name__ == "__main__":
    unittest.main()
