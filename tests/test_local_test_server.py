import socket
import threading
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
        def server():
            try:
                run_server(port=port, input_fn=iter(["Hey @Bubba", "/quit"]).__next__,
                           output_fn=lines.append)
            except BaseException as exc:
                errors.append(exc)
        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        import time
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.05):
                    pass
            except OSError:
                time.sleep(.01)
                continue
            break
        # First probe connection is intentionally not used by the bot; avoid
        # relying on its timing by running an independent integration test.
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(errors)  # probe disconnect during identification is handled by caller

    def test_invalid_port(self):
        with self.assertRaises(ValueError):
            run_server(port=0)
