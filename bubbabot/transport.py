"""Local-only TCP transport for offline integration tests.

This is NOT an authenticated MRC network client. Only numeric loopback
addresses are accepted, and the caller controls any retry schedule.
"""
import ipaddress
import socket
import time


MAX_LINE_BYTES = 8192


def require_loopback(host: str) -> str:
    """Reject hostnames, public/private network addresses, and non-loopback IPs."""
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("transport requires a numeric loopback IP") from exc
    if not address.is_loopback:
        raise ValueError("transport is restricted to loopback")
    return str(address)


class LocalTCPTransport:
    def __init__(self, host="127.0.0.1", port=0, *, timeout=2.0,
                 retry_delay=0.1, max_attempts=3, sleep=None):
        self.host = require_loopback(host)
        if not isinstance(port, int) or isinstance(port, bool) or not 0 < port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if timeout <= 0 or retry_delay < 0 or max_attempts < 1:
            raise ValueError("invalid connection settings")
        self.port = port
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_attempts = max_attempts
        self.sleep = sleep or time.sleep

    def connect(self):
        """Return connected socket or raise after bounded retries."""
        last_error = None
        for attempt in range(self.max_attempts):
            try:
                connection = socket.create_connection(
                    (self.host, self.port), timeout=self.timeout
                )
                connection.settimeout(self.timeout)
                return connection
            except OSError as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    self.sleep(self.retry_delay)
        raise ConnectionError(
            f"local test server unavailable after {self.max_attempts} attempts"
        ) from last_error

    def exchange(self, incoming_lines, *, max_line_bytes=MAX_LINE_BYTES):
        """Yield complete UTF-8 response lines for a single local TCP session.

        Caller supplies outbound lines; server responses are read until EOF.
        Reconnection is deliberately limited to connection establishment:
        messages are never automatically replayed after disconnect.
        """
        if max_line_bytes < 1:
            raise ValueError("invalid line limit")
        with self.connect() as connection:
            for line in incoming_lines:
                if not isinstance(line, str) or not line.endswith("\n"):
                    raise ValueError("outgoing lines must end in newline")
                encoded = line.encode("utf-8")
                if len(encoded) > max_line_bytes:
                    raise ValueError("outgoing line too long")
                connection.sendall(encoded)
            connection.shutdown(socket.SHUT_WR)
            pending = bytearray()
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    if pending:
                        raise ValueError("unterminated incoming line")
                    return
                pending.extend(chunk)
                if len(pending) > max_line_bytes and b"\n" not in pending:
                    raise ValueError("incoming line too long")
                while b"\n" in pending:
                    index = pending.index(b"\n") + 1
                    if index > max_line_bytes:
                        raise ValueError("incoming line too long")
                    raw = bytes(pending[:index])
                    del pending[:index]
                    yield raw.decode("utf-8")
                if len(pending) > max_line_bytes:
                    raise ValueError("incoming line too long")
