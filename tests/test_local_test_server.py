import socket
import threading
import time
import unittest

from bubbabot.local_test_server import run_server
from bubbabot.mrc_client_session import LocalMRCSession
from bubbabot.mrc_handshake import ClientIdentity
from bubbabot.engine import BubbaEngine
from bubbabot.session import OfflineSession
from bubbabot.transport import LocalTCPTransport


class InteractiveMockTests(unittest.TestCase):
    def test_interactive_mock_server_and_bot(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        lines = []
        errors = []
        messages = iter(["Hey @Bubba", "/quit"])

        def server():
            try:
                run_server(port=port,
                           input_fn=lambda prompt: next(messages),
                           output_fn=lines.append)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        for _ in range(200):
            if lines:
                break
            time.sleep(.01)
        self.assertTrue(lines, "mock server did not start")
        engine = BubbaEngine({"BubbaRoom"}, cooldown_seconds=0)
        session = OfflineSession(engine)
        client = LocalMRCSession(
            LocalTCPTransport(port=port, timeout=3, max_attempts=1),
            ClientIdentity("BubbaTest"), session
        )
        result = client.run()
        thread.join(timeout=4)
        self.assertFalse(thread.is_alive())
        self.assertFalse(errors, errors)
        self.assertEqual(result["replies"], 1)
        self.assertTrue(any("Howdy, Dave!" in line for line in lines))

    def test_invalid_port(self):
        with self.assertRaises(ValueError):
            run_server(port=0)


if __name__ == "__main__":
    unittest.main()
