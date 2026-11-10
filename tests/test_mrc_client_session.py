"""Real local TCP integration tests; no public connections or API calls."""
import socket
import threading
import unittest

from bubbabot.engine import BubbaEngine
from bubbabot.mrc_client_session import LocalMRCSession
from bubbabot.mrc_handshake import ClientIdentity
from bubbabot.session import OfflineSession
from bubbabot.transport import LocalTCPTransport


class SessionIntegrationTests(unittest.TestCase):
    def test_full_handshake_heartbeat_chat_and_shutdown(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        port = listener.getsockname()[1]
        observed = []
        errors = []

        def server():
            try:
                with listener:
                    connection, _ = listener.accept()
                    with connection:
                        connection.settimeout(3)
                        expected = b"TestBBS~MYSTIC/Windows/AMD64/1.3.7"
                        initial = bytearray()
                        while len(initial) < len(expected):
                            initial.extend(connection.recv(len(expected) - len(initial)))
                        observed.append(bytes(initial))
                        self.assertEqual(bytes(initial), expected)
                        # Split the server ping to test TCP reassembly.
                        connection.sendall(b"SERVER~~~ALL~~~PI")
                        connection.sendall(b"NG~\n")
                        observed.append(self._line(connection))
                        connection.sendall(
                            b"Dave~DavesBBS~BubbaRoom~ALL~~BubbaRoom~Hey @Bubba!~\n"
                        )
                        observed.append(self._line(connection))
                        connection.sendall(b"SERVER~~~ALL~~~STATS~\n")
                        observed.append(self._line(connection))
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        engine = BubbaEngine({"BubbaRoom"}, cooldown_seconds=0)
        chat = OfflineSession(engine)
        client = LocalMRCSession(
            LocalTCPTransport(port=port, timeout=3, max_attempts=1),
            ClientIdentity("TestBBS"), chat, process_id=42, max_messages=3
        )
        result = client.run()
        thread.join(timeout=4)
        self.assertFalse(thread.is_alive())
        if errors:
            raise errors[0]
        self.assertEqual(result, {"messages": 3, "replies": 1})
        self.assertEqual(observed[1],
                         "CLIENT~TestBBS~42~SERVER~~~IMALIVE:TestBBS~\n")
        self.assertIn("Howdy, Dave!", observed[2])
        self.assertEqual(observed[3],
                         "CLIENT~TestBBS~~SERVER~~~SHUTDOWN~\n")

    @staticmethod
    def _line(connection):
        data = bytearray()
        while not data.endswith(b"\n"):
            chunk = connection.recv(1)
            if not chunk:
                raise EOFError("client disconnected")
            data.extend(chunk)
        return data.decode("utf-8")

    def test_rejects_nonlocal_transport(self):
        with self.assertRaises(ValueError):
            LocalTCPTransport(host="8.8.8.8", port=5001)


if __name__ == "__main__":
    unittest.main()
