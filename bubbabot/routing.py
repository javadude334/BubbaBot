"""Offline decision logic for whether Bubba should respond."""

import re

from .protocol import Packet


MENTION = re.compile(r"(?<![A-Za-z0-9_])@?bubba(?![A-Za-z0-9_])", re.I)


def should_reply(packet: Packet, *, allowed_rooms: set[str], bot_name: str = "Bubba") -> bool:
    """Reply only to addressed requests in explicitly allowed rooms.

    Allowed rooms are matched case-insensitively. Direct-message routing
    needs separate server-protocol verification before it is enabled.
    """
    if packet.from_user.casefold() in {"server", "client", bot_name.casefold()}:
        return False
    if packet.from_site.casefold() == "bubbabot":
        return False
    if packet.from_room.casefold() not in {room.casefold() for room in allowed_rooms}:
        return False
    if packet.to_user and packet.to_user.casefold() not in {"all", bot_name.casefold()}:
        return False
    return bool(MENTION.search(packet.message))
