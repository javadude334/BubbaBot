"""Minimal MRC packet parsing and encoding, based on the uploaded v1.3.7 client.

Seven positional fields plus an optional trailing delimiter are expected.
This module does not implement MRC network connectivity.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Packet:
    from_user: str
    from_site: str
    from_room: str
    to_user: str
    to_site: str
    to_room: str
    message: str


def parse_packet(line: str) -> Packet:
    """Parse exactly seven MRC fields; reject malformed or ambiguous records."""
    if not isinstance(line, str):
        raise TypeError("MRC packet must be a string")
    fields = line.rstrip("\r\n").split("~")
    if len(fields) == 8 and fields[-1] == "":
        fields.pop()
    if len(fields) != 7:
        raise ValueError("expected seven MRC fields")
    if not fields[0]:
        raise ValueError("missing sender")
    return Packet(*fields)


def encode_packet(packet: Packet) -> str:
    """Encode a packet as a newline-terminated MRC line."""
    fields = (
        packet.from_user,
        packet.from_site,
        packet.from_room,
        packet.to_user,
        packet.to_site,
        packet.to_room,
        packet.message,
    )
    if any("\n" in field or "\r" in field or "~" in field for field in fields):
        raise ValueError("MRC field contains reserved character")
    return "~".join(fields) + "~\n"
