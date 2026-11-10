"""Standalone bot identity and room configuration for offline simulations.

This profile is not a public MRC authentication credential or authorization.
"""
from dataclasses import dataclass, field
import re

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,31}$")
_ROOM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")


def normalize_room(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid room")
    room = value.removeprefix("#")
    if not _ROOM.fullmatch(room):
        raise ValueError("invalid room")
    return room


@dataclass(frozen=True)
class BotProfile:
    name: str = "Bubba"
    site: str = "BubbaBot"
    room: str = "Bubba"
    _room_key: str = field(init=False, repr=False)

    def __post_init__(self):
        if not _NAME.fullmatch(self.name) or not _NAME.fullmatch(self.site):
            raise ValueError("invalid bot identity")
        room = normalize_room(self.room)
        object.__setattr__(self, "room", room)
        object.__setattr__(self, "_room_key", room.casefold())

    def accepts_room(self, room: str) -> bool:
        try:
            return normalize_room(room).casefold() == self._room_key
        except ValueError:
            return False
