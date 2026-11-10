import socket
import threading
import unittest

from bubbabot.transport import LocalTCPTransport, require_loopback


class TransportTests(unittest.TestCase):
    def test_rejects_non_loopback(self):
        for host in ("example.com", "192.168.1.5", "8.8.8.8", "0.0.0.0"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                require_loopback(host)

    def test_rejects_invalid_settings(self):
        with self.assertRaises(ValueError):
            LocalTCPTransport(port=0)
        with self.assertRaises(ValueError):
            LocalTCPTransport(port=5000, max_attempts=0)

    def test_connection_failure_is_bounded(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        listener.close()
        sleeps = []
        transport = LocalTCPTransport(port=port, timeout=0.1,
                                      retry_delay=0, max_attempts=2,
                                      sleep=lambda value: sleeps.append(value))
        with self.assertRaises(ConnectionError):
            transport.connect()
        self.assertEqual(len(sleeps), 1)

    def test_local_roundtrip(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.settimeout(3)
        port = server.getsockname()[1]
        received = []
        errors = []

        def serve():
            try:
                with server:
                    conn, _ = server.accept()
                    with conn:
                        conn.settimeout(3)
                        chunks = []
                        while True:
                            part = conn.recv(1024)
                            if not part:
                                break
                            chunks.append(part)
                        received.append(b"".join(chunks))
                        conn.sendall(b"server~test~room~ALL~~room~hello~\n")
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        client = LocalTCPTransport(port=port, timeout=2, max_attempts=1)
        result = list(client.exchange(["client~test~room~ALL~~room~hi~\n"]))
        thread.join(timeout=4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(received, [b"client~test~room~ALL~~room~hi~\n"])
        self.assertEqual(result, ["server~test~room~ALL~~room~hello~\n"])


if __name__ == "__main__":
    unittest.main()
