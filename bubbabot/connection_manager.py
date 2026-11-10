"""Receive-only reconnecting connection manager for loopback test servers.

No live MRC authentication or outbound chat is implemented. A new TCP
connection starts with no queued messages, preventing automatic replay.
"""
import socket
import time

from .transport import LocalTCPTransport, MAX_LINE_BYTES


class ConnectionManager:
    def __init__(self, transport: LocalTCPTransport, *, initial_delay=0.1,
                 max_delay=5.0, max_sessions=3, sleep=None):
        if initial_delay < 0 or max_delay < initial_delay or max_sessions < 1:
            raise ValueError("invalid reconnection settings")
        self.transport = transport
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_sessions = max_sessions
        self.sleep = sleep or time.sleep

    def run(self, on_line):
        """Connect up to max_sessions times and report received complete lines.

        A clean EOF or socket error triggers a fresh connection. Timeouts are
        treated as failures, not idle heartbeats. No messages are ever resent.
        The callback may raise to stop the manager; its errors are not hidden.
        """
        delay = self.initial_delay
        completed = 0
        for attempt in range(self.max_sessions):
            try:
                with self.transport.connect() as connection:
                    completed += 1
                    pending = bytearray()
                    while True:
                        chunk = connection.recv(4096)
                        if not chunk:
                            if pending:
                                raise ValueError("unterminated incoming line")
                            break
                        pending.extend(chunk)
                        while b"\n" in pending:
                            index = pending.index(b"\n") + 1
                            if index > MAX_LINE_BYTES:
                                raise ValueError("incoming line too long")
                            line = bytes(pending[:index]).decode("utf-8")
                            del pending[:index]
                            on_line(line)
                        if len(pending) > MAX_LINE_BYTES:
                            raise ValueError("incoming line too long")
            except (OSError, ConnectionError, ValueError, UnicodeError):
                # Only transport/framing failures are recoverable.
                pass
            if attempt + 1 < self.max_sessions:
                self.sleep(delay)
                delay = min(self.max_delay, delay * 2) if delay else 0
        return completed
