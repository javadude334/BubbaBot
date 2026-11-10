"""Interactive loopback-only mock MRC server. Never binds a public interface."""
import argparse
import socket

from .protocol import Packet, encode_packet
from .transport import MAX_LINE_BYTES


def read_line(connection):
    data = bytearray()
    while True:
        part = connection.recv(1)
        if not part:
            raise EOFError("client disconnected")
        data.extend(part)
        if len(data) > MAX_LINE_BYTES:
            raise ValueError("incoming packet too long")
        if part == b"\n":
            return data.decode("utf-8")


def run_server(port=5001, room="BubbaRoom", user="Dave", site="DavesBBS",
               *, input_fn=input, output_fn=print):
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("invalid port")
    for value in (room, user, site):
        if not value or any(char in value for char in "~\r\n"):
            raise ValueError("invalid packet field")
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(1)
        output_fn(f"Mock MRC server listening on 127.0.0.1:{port} (LOCAL ONLY)")
        output_fn("Start run-bubba-local.cmd in another terminal.")
        with listener.accept()[0] as connection:
            output_fn("TCP client accepted; waiting for identification...")
            connection.settimeout(10)
            # The legacy client sends raw identification without a newline.
            # A single recv may contain a partial identification.
            identity = bytearray()
            while b"/1.3.7" not in identity:
                chunk = connection.recv(256)
                if not chunk:
                    raise EOFError("client disconnected during identification")
                identity.extend(chunk)
                if len(identity) > 512:
                    raise ValueError("invalid client identification")
            output_fn("Connected: " + identity.decode("utf-8", errors="replace"))
            connection.sendall(b"SERVER~~~ALL~~~PING~\n")
            output_fn("Heartbeat: " + read_line(connection).strip())
            # The independent local runner announces its room presence.
            # Older mock clients may omit this packet.
            connection.settimeout(0.3)
            try:
                presence = read_line(connection)
                if not presence.endswith("~IAMHERE~\n"):
                    output_fn("Unexpected presence packet: " + presence.strip())
                else:
                    output_fn("Room presence: " + presence.strip())
            except socket.timeout:
                pass
            connection.settimeout(10)
            output_fn(f"Type a message for #{room} (e.g. Hey @Bubba), or /quit.")
            while True:
                try:
                    message = input_fn("MRC> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if message.casefold() in {"/quit", "/exit"}:
                    break
                if not message:
                    continue
                if any(char in message for char in "~\r\n"):
                    output_fn("Message cannot contain tilde or newline.")
                    continue
                packet = Packet(user, site, room, "ALL", "", room, message)
                connection.sendall(encode_packet(packet).encode("utf-8"))
                try:
                    connection.settimeout(1.5)
                    response = read_line(connection)
                    output_fn("Bubba: " + response.split("~")[6])
                except socket.timeout:
                    output_fn("(No reply: try addressing @Bubba; cooldown may apply.)")
                except EOFError:
                    output_fn("Bubba disconnected.")
                    break
    output_fn("Mock server stopped.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Interactive local-only MRC mock server")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--room", default="BubbaRoom")
    args = parser.parse_args(argv)
    run_server(port=args.port, room=args.room)


if __name__ == "__main__":
    main()
