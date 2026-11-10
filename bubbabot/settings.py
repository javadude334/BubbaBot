"""Validated offline configuration; no live network endpoints or credentials."""
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    room: str = "BubbaRoom"
    site: str = "BubbaTest"
    host: str = "127.0.0.1"
    port: int = 5001
    cooldown_seconds: int = 30
    max_replies_per_hour: int = 20

    def __post_init__(self):
        from .transport import require_loopback
        require_loopback(self.host)
        if not isinstance(self.port, int) or isinstance(self.port, bool) or not 1 <= self.port <= 65535:
            raise ValueError("invalid port")
        if not self.room or not self.site or any(c in s for s in (self.room, self.site) for c in "~\r\n"):
            raise ValueError("invalid room or site")
        if self.cooldown_seconds < 0 or self.max_replies_per_hour < 1:
            raise ValueError("invalid limits")


def load_settings(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings must be a JSON object")
    permitted = set(Settings.__dataclass_fields__)
    unknown = set(data) - permitted
    if unknown:
        raise ValueError("unknown settings: " + ", ".join(sorted(unknown)))
    return Settings(**data)
