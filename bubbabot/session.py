"""Offline line-stream adapter. Deliberately contains no network code."""
from .engine import BubbaEngine
from .protocol import Packet, encode_packet, parse_packet


class OfflineSession:
    """Read incoming MRC-formatted lines and write simulated bot replies."""

    def __init__(self, engine: BubbaEngine, *, bot_name="Bubba", bot_site="BubbaBot"):
        self.engine = engine
        self.bot_name = bot_name
        self.bot_site = bot_site

    def handle_line(self, line: str) -> str | None:
        """Return an encoded reply or None. Malformed input is ignored."""
        try:
            packet = parse_packet(line)
        except (ValueError, TypeError):
            return None
        reply = self.engine.process(packet)
        if reply is None:
            return None
        return encode_packet(Packet(
            from_user=self.bot_name,
            from_site=self.bot_site,
            from_room=reply.room,
            to_user="ALL",
            to_site="",
            to_room=reply.room,
            message=reply.text,
        ))

    def run(self, incoming, outgoing):
        """Process an iterable of lines. No sockets, sleeps, or API calls."""
        for line in incoming:
            response = self.handle_line(line)
            if response is not None:
                outgoing.write(response)
                outgoing.flush()
