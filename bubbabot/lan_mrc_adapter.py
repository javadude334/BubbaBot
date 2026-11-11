"""Experimental LAN MRC adapter for the existing Ubuntu BubbaBot.

Run with the existing bubbabot Python environment, not the official SDK runner.
Only #bubba mentions are answered. Do not expose the Go gateway to the Internet.
"""
import os
import socket
import sys
import time
from collections import defaultdict

from .chat import converse
from .engine import BubbaEngine
from .protocol import Packet

BOT_NAME = "Bubba"
BOT_SITE = "BubbaBot_Ubuntu"
ROOM = "bubba"
MAX_HISTORY = 12


def clean(value):
    """Convert AI text to printable ASCII suitable for Mystic MRC terminals."""
    import unicodedata

    substitutions = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...",
        "\u00a0": " ", "\u2022": "*",
    }
    for original, replacement in substitutions.items():
        value = value.replace(original, replacement)
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", errors="ignore").decode("ascii")
    return " ".join(value.replace("~", " ").split())


def encode(fields):
    return "~".join(clean(str(field)) for field in fields) + "~\n"


def main():
    host = os.environ.get("LOCAL_MRC_HOST", "").strip()
    port = int(os.environ.get("LOCAL_MRC_PORT", "5000"))
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("BUBBABOT_AI_MODEL", "gpt-4o-mini")
    if not host or not key:
        raise SystemExit("LOCAL_MRC_HOST and OPENAI_API_KEY are required")
    if not 1 <= port <= 65535:
        raise SystemExit("Invalid LOCAL_MRC_PORT")
    engine = BubbaEngine({ROOM}, cooldown_seconds=30, max_replies_per_hour=20)
    histories = defaultdict(list)
    attempts = 0
    # This limit is per process lifetime, not a billing limit.
    while True:
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                sock.settimeout(None)
                stream = sock.makefile("rb")
                sock.sendall((BOT_SITE + "~Python/BubbaBot/0.1\n").encode())
                sock.sendall(encode((BOT_NAME, BOT_SITE, ROOM, "SERVER", "", ROOM, "IAMHERE")).encode())
                print("Bubba connected to local MRC gateway", flush=True)
                while True:
                    raw = stream.readline(65537)
                    if not raw or len(raw) > 65536:
                        break
                    try:
                        parts = raw.decode("utf-8", errors="replace").rstrip("\r\n").split("~", 7)
                        if len(parts) < 7:
                            continue
                        user, site, room, to_user, to_site, to_room, message = parts[:7]
                        message = message.rstrip("~")
                        # No PM support until routing is verified.
                        if to_user.upper() not in ("", "ALL"):
                            continue
                        if room.lstrip("#").casefold() != ROOM:
                            continue
                        if user.casefold() in ("bubba", "bubbabot", "server", "client"):
                            continue
                        if site.casefold() == BOT_SITE.casefold():
                            continue
                        packet = Packet(user, site, room.lstrip("#"), "ALL", "", room.lstrip("#"), message)
                        allowed = engine.process(packet)
                        if allowed is None:
                            continue
                        if attempts >= 100:
                            print("Bubba request limit reached; restart required", flush=True)
                            continue
                        attempts += 1
                        sender_key = (site.casefold(), user.casefold())
                        history = histories[sender_key]
                        candidate = history + [{"role": "user", "content": message[:500]}]
                        try:
                            reply, usage = converse(candidate, api_key=key, model=model)
                        except Exception as exc:
                            print("AI request failed: " + type(exc).__name__, file=sys.stderr, flush=True)
                            continue
                        histories[sender_key] = (candidate + [{"role": "assistant", "content": reply}])[-MAX_HISTORY:]
                        reply = clean(reply)[:220]
                        if reply:
                            sock.sendall(encode((BOT_NAME, BOT_SITE, ROOM, "", "", ROOM, reply)).encode())
                    except (ValueError, UnicodeError) as exc:
                        print("Ignored malformed packet: " + type(exc).__name__, file=sys.stderr, flush=True)
        except (OSError, ConnectionError) as exc:
            print("Gateway connection lost: " + type(exc).__name__, file=sys.stderr, flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
