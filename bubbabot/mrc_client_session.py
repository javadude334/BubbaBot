"""Offline MRC session runner over an explicitly loopback-only TCP transport.

Not a production MRC client: identity and authorization must be approved before
any live connection. A single socket handles control and chat responses.
"""
import socket

from .mrc_handshake import identification, im_alive, server_ping, shutdown
from .transport import LocalTCPTransport
from .framing import MRCLineFramer


class LocalMRCSession:
    def __init__(self, transport: LocalTCPTransport, identity, chat_session, *,
                 process_id=1, max_messages=100):
        if not isinstance(transport, LocalTCPTransport):
            raise TypeError("only LocalTCPTransport is supported")
        if max_messages < 1:
            raise ValueError("max_messages must be positive")
        self.transport = transport
        self.identity = identity
        self.chat_session = chat_session
        self.process_id = process_id
        self.max_messages = max_messages

    def run(self):
        """Connect once; send raw identity, answer pings and chat, then close.

        EOF terminates a session. Messages are never queued for reconnect.
        Incoming lines are framed before parsing, even across recv boundaries.
        """
        replies = 0
        messages = 0
        with self.transport.connect() as connection:
            connection.sendall(identification(self.identity))
            framer = MRCLineFramer()
            while messages < self.max_messages:
                try:
                    chunk = connection.recv(4096)
                except socket.timeout:
                    # Idle is normal while a human types in the mock MRC room.
                    # The socket remains open; no packet is replayed or invented.
                    continue
                if not chunk:
                    framer.finish()
                    break
                for line in framer.feed(chunk):
                    if messages >= self.max_messages:
                        break
                    messages += 1
                    if server_ping(line):
                        connection.sendall(im_alive(self.identity, self.process_id).encode("utf-8"))
                    else:
                        response = self.chat_session.handle_line(line)
                        if response:
                            connection.sendall(response.encode("utf-8"))
                            replies += 1
            # Explicit shutdown is sent only when server has not already closed.
            if messages >= self.max_messages:
                try:
                    connection.sendall(shutdown(self.identity).encode("utf-8"))
                except OSError:
                    pass
        return {"messages": messages, "replies": replies}
