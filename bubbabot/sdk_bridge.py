"""SDK-independent policy boundary for a future approved MRC Mode 1 connector.

No networking, credentials, or guessed SDK API methods. The official SDK
adapter will call this bridge after its documented event mapping is verified.
"""
from dataclasses import dataclass

from .bot_profile import BotProfile
from .room_manager import OfflineRoomManager
from .protocol import Packet, encode_packet, parse_packet


@dataclass(frozen=True)
class IncomingChat:
    user: str
    site: str
    room: str
    text: str


@dataclass(frozen=True)
class OutgoingChat:
    room: str
    text: str


class SDKBridge:
    """Pure event-to-reply conversion, with a fail-closed room policy."""

    def __init__(self, profile=None, *, cooldown_seconds=30,
                 max_replies_per_hour=20):
        self.profile = profile or BotProfile(room="Bubba")
        if self.profile.room.casefold() == "lobby":
            raise ValueError("MRC policy prohibits bot participation in lobby")
        self.manager = OfflineRoomManager(
            self.profile, cooldown_seconds=cooldown_seconds,
            max_replies_per_hour=max_replies_per_hour
        )

    def handle(self, event: IncomingChat):
        if not isinstance(event, IncomingChat):
            raise TypeError("expected IncomingChat")
        room = event.room.lstrip("#")
        if room.casefold() == "lobby" or not self.profile.accepts_room(room):
            return None
        # Keep the existing, tested mention/cooldown/self-reply engine.
        packet = Packet(event.user, event.site, room, "ALL", "", room, event.text)
        encoded = self.manager.handle_line(encode_packet(packet))
        if not encoded:
            return None
        reply = parse_packet(encoded)
        return OutgoingChat(room=reply.from_room, text=reply.message)
