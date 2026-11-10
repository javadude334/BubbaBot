"""End-to-end independent identity, multiple BBS users and reconnects, loopback only."""
import socket
import threading
import unittest

from bubbabot.bot_profile import BotProfile
from bubbabot.room_manager import OfflineRoomManager
from bubbabot.mrc_client_session import LocalMRCSession
from bubbabot.mrc_handshake import ClientIdentity
from bubbabot.reconnecting_runner import run_reconnecting
from bubbabot.transport import LocalTCPTransport
from bubbabot.protocol import Packet, encode_packet, parse_packet


def read_line(conn):
    result = bytearray()
    while not result.endswith(b"\n"):
        chunk = conn.recv(1)
        if not chunk:
            raise EOFError("unexpected disconnect")
        result.extend(chunk)
    return result.decode("utf-8")


class StandaloneSimulationTests(unittest.TestCase):
    def test_two_sessions_multiple_users_no_replay(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(2)
        listener.settimeout(4)
        port = listener.getsockname()[1]
        errors = []
        observed = []

        def server():
            try:
                with listener:
                    for index in range(2):
                        connection, _ = listener.accept()
                        with connection:
                            connection.settimeout(3)
                            identity = b"BubbaTest~MYSTIC/Windows/AMD64/1.3.7"
                            received = bytearray()
                            while len(received) < len(identity):
                                chunk = connection.recv(len(identity) - len(received))
                                if not chunk:
                                    raise EOFError("missing identity")
                                received.extend(chunk)
                            self.assertEqual(bytes(received), identity)
                            connection.sendall(b"SERVER~~~ALL~~~PING~\n")
                            heartbeat = parse_packet(read_line(connection))
                            self.assertEqual(heartbeat.message, "IMALIVE:BubbaTest")

                            if index == 0:
                                inputs = [
                                    Packet("Dave", "DavesBBS", "Bubba", "ALL", "", "Bubba", "Hey @Bubba"),
                                    Packet("Alice", "AnotherBBS", "Bubba", "ALL", "", "Bubba", "Hello Bubba"),
                                    Packet("Bob", "OtherBBS", "Lobby", "ALL", "", "Lobby", "Hey Bubba"),
                                ]
                            else:
                                inputs = [
                                    Packet("Carol", "ThirdBBS", "Bubba", "ALL", "", "Bubba", "Hi Bubba"),
                                    Packet("Bubba", "BubbaBot", "Bubba", "ALL", "", "Bubba", "Hey Bubba"),
                                    Packet("SERVER", "", "", "ALL", "", "", "STATS"),
                                ]
                            for packet in inputs:
                                connection.sendall(encode_packet(packet).encode("utf-8"))
                                if packet.from_user in {"Dave", "Alice", "Carol"}:
                                    response = parse_packet(read_line(connection))
                                    self.assertEqual(response.from_user, "Bubba")
                                    self.assertEqual(response.from_site, "BubbaBot")
                                    self.assertEqual(response.from_room, "Bubba")
                                    self.assertIn(packet.from_user, response.message)
                                    observed.append(packet.from_user)
                            # Session limit reached: client sends shutdown before closing.
                            self.assertEqual(parse_packet(read_line(connection)).message, "SHUTDOWN")
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        profile = BotProfile(name="Bubba", site="BubbaBot", room="#Bubba")
        manager = OfflineRoomManager(profile, cooldown_seconds=0)
        def make_session():
            return LocalMRCSession(
                LocalTCPTransport(host="127.0.0.1", port=port, timeout=3, max_attempts=1),
                ClientIdentity(site="BubbaTest"), manager.session, max_messages=4
            )
        try:
            result = run_reconnecting(make_session, max_sessions=2,
                                      initial_delay=0, max_delay=0, sleep=lambda _: None)
        finally:
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "mock server did not terminate")
        if errors:
            raise errors[0]
        self.assertEqual(result, {"sessions": 2, "messages": 8, "replies": 3})
        self.assertEqual(observed, ["Dave", "Alice", "Carol"])


if __name__ == "__main__":
    unittest.main()
