"""MRC v1.3.7 client handshake/control packet builders.

Derived from the uploaded Phenom Productions mrc_client.py source.
Offline only: no sockets, no authentication claims, and no live connections.
"""
from dataclasses import dataclass

from .protocol import Packet, encode_packet, parse_packet


@dataclass(frozen=True)
class ClientIdentity:
    site: str
    platform: str = "MYSTIC"
    system: str = "Windows"
    architecture: str = "AMD64"
    version: str = "1.3.7"
    capabilities: str = "MCI CTCP SSL"

    def __post_init__(self):
        for value in (self.site, self.platform, self.system,
                      self.architecture, self.version, self.capabilities):
            if not value or any(char in value for char in "~\r\n"):
                raise ValueError("invalid MRC identity field")


def identification(identity: ClientIdentity) -> bytes:
    """Original client sends this raw, without a line terminator."""
    return (f"{identity.site}~{identity.platform}/{identity.system}/"
            f"{identity.architecture}/{identity.version}").encode("utf-8")


def control(identity: ClientIdentity, message: str, *, room="", target_site="") -> str:
    return encode_packet(Packet(
        "CLIENT", identity.site, room, "SERVER", target_site, "", message
    ))


def im_alive(identity: ClientIdentity, process_id: int) -> str:
    if process_id < 0:
        raise ValueError("invalid process ID")
    return control(identity, f"IMALIVE:{identity.site}", room=str(process_id))


def capabilities(identity: ClientIdentity, client_hash: str) -> str:
    return control(identity, f"CAPABILITIES:{identity.capabilities}",
                   room=client_hash)


def shutdown(identity: ClientIdentity) -> str:
    return control(identity, "SHUTDOWN")


def stats_request(identity: ClientIdentity) -> str:
    return control(identity, "STATS")


def server_ping(line: str) -> bool:
    """Only the server sender and ping command trigger a heartbeat."""
    try:
        packet = parse_packet(line)
    except (ValueError, TypeError):
        return False
    return packet.from_user == "SERVER" and packet.message.casefold() == "ping"
