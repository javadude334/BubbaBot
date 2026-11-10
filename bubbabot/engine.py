"""Offline Bubba chat engine. No sockets, API calls, or external dependencies."""
from collections import deque
from dataclasses import dataclass
import time

from .protocol import Packet
from .routing import should_reply


@dataclass(frozen=True)
class Reply:
    recipient: str
    room: str
    text: str


class BubbaEngine:
    """Apply room, mention, length and per-sender rate limits before replying."""

    def __init__(self, allowed_rooms, *, cooldown_seconds=30, max_message_chars=500,
                 max_replies_per_hour=20, clock=None):
        if cooldown_seconds < 0 or max_message_chars < 1 or max_replies_per_hour < 1:
            raise ValueError("invalid engine limits")
        self.allowed_rooms = set(allowed_rooms)
        self.cooldown_seconds = cooldown_seconds
        self.max_message_chars = max_message_chars
        self.max_replies_per_hour = max_replies_per_hour
        self.clock = clock or time.monotonic
        self._last_reply = {}
        self._reply_times = deque()

    def process(self, packet: Packet) -> Reply | None:
        """Produce a deterministic test response, never an AI response."""
        if not should_reply(packet, allowed_rooms=self.allowed_rooms):
            return None
        if not packet.message.strip() or len(packet.message) > self.max_message_chars:
            return None
        now = self.clock()
        key = (packet.from_site.casefold(), packet.from_user.casefold())
        previous = self._last_reply.get(key)
        if previous is not None and now - previous < self.cooldown_seconds:
            return None
        while self._reply_times and now - self._reply_times[0] >= 3600:
            self._reply_times.popleft()
        if len(self._reply_times) >= self.max_replies_per_hour:
            return None
        self._last_reply[key] = now
        self._reply_times.append(now)
        return Reply(
            recipient=packet.from_user,
            room=packet.from_room,
            text=f"Howdy, {packet.from_user}! I'm Bubba, an experimental AI bot. "
                 "I'm running in offline test mode right now.",
        )
