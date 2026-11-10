import socket
import threading
import unittest

from bubbabot.connection_manager import ConnectionManager
from bubbabot.transport import LocalTCPTransport


class ConnectionManagerTests(unittest.TestCase):
    def test_settings_validation(self):
        transport = LocalTCPTransport(port=12345, max_attempts=1)
        with self.assertRaises(ValueError):
            ConnectionManager(transport, max_sessions=0)
        with self.assertRaises(ValueError):
            ConnectionManager(transport, initial_delay=2, max_delay=1)

    def test_reconnects_after_disconnect(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(2)
        listener.settimeout(3)
        port = listener.getsockname()[1]
        errors = []

        def serve():
            try:
                with listener:
                    for payload in (b"first\n", b"second\n"):
                        conn, _ = listener.accept()
                        with conn:
                            conn.sendall(payload)
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        lines = []
        transport = LocalTCPTransport(port=port, timeout=1, max_attempts=1)
        manager = ConnectionManager(transport, max_sessions=2,
                                    initial_delay=0, max_delay=0,
                                    sleep=lambda _: None)
        count = manager.run(lines.append)
        worker.join(timeout=4)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(count, 2)
        self.assertEqual(lines, ["first\n", "second\n"])

    def test_backoff_on_refused_connection(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        listener.close()
        delays = []
        transport = LocalTCPTransport(port=port, timeout=0.1, max_attempts=1)
        manager = ConnectionManager(transport, initial_delay=0.25,
                                    max_delay=0.5, max_sessions=4,
                                    sleep=delays.append)
        self.assertEqual(manager.run(lambda line: None), 0)
        self.assertEqual(delays, [0.25, 0.5, 0.5])

    def test_callback_error_is_not_swallowed(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        port = listener.getsockname()[1]

        def serve():
            with listener:
                conn, _ = listener.accept()
                with conn:
                    conn.sendall(b"hello\n")

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        manager = ConnectionManager(
            LocalTCPTransport(port=port, timeout=1, max_attempts=1),
            max_sessions=1)
        with self.assertRaises(RuntimeError):
            manager.run(lambda line: (_ for _ in ()).throw(RuntimeError("stop")))
        worker.join(timeout=4)


if __name__ == "__main__":
    unittest.main()
