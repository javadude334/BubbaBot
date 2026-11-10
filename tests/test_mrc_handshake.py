import unittest

from bubbabot.mrc_handshake import (
    ClientIdentity, identification, im_alive, capabilities,
    shutdown, stats_request, server_ping,
)
from bubbabot.protocol import parse_packet


class HandshakeTests(unittest.TestCase):
    def setUp(self):
        self.identity = ClientIdentity(site="TestBBS")

    def test_raw_identification_has_no_newline(self):
        self.assertEqual(
            identification(self.identity),
            b"TestBBS~MYSTIC/Windows/AMD64/1.3.7"
        )

    def test_heartbeat_matches_reference(self):
        self.assertEqual(
            im_alive(self.identity, 123),
            "CLIENT~TestBBS~123~SERVER~~~IMALIVE:TestBBS~\n"
        )

    def test_capabilities_matches_reference(self):
        self.assertEqual(
            capabilities(self.identity, "hash"),
            "CLIENT~TestBBS~hash~SERVER~~~CAPABILITIES:MCI CTCP SSL~\n"
        )

    def test_shutdown_and_stats(self):
        self.assertEqual(parse_packet(shutdown(self.identity)).message, "SHUTDOWN")
        self.assertEqual(parse_packet(stats_request(self.identity)).message, "STATS")

    def test_server_ping(self):
        self.assertTrue(server_ping("SERVER~~~ALL~~~PING~\n"))
        self.assertFalse(server_ping("Dave~TestBBS~lobby~ALL~~lobby~PING~\n"))
        self.assertFalse(server_ping("not a packet"))

    def test_rejects_reserved_identity_characters(self):
        with self.assertRaises(ValueError):
            ClientIdentity(site="Bad~Site")


if __name__ == "__main__":
    unittest.main()
