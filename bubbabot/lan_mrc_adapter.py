"""Experimental LAN MRC adapter for the existing Ubuntu BubbaBot.

Run with the existing bubbabot Python environment, not the official SDK runner.
In #bubba, a mention starts a time-limited per-user conversation.
Do not expose the Go gateway to the Internet.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import socket
import sys
import time
from collections import defaultdict

from .chat import converse
from .ai_provider import INSTRUCTIONS
from .engine import BubbaEngine
from .protocol import Packet
from .routing import MENTION

BOT_NAME = "Bubba"
BOT_SITE = "BubbaBot_Ubuntu"
ROOM = "bubba"
MAX_HISTORY = 12
SESSION_SECONDS = 600
FOLLOWUP_COOLDOWN_SECONDS = 5

MAX_REPLY_CHARS = 220
BUBBA_STYLE = (
    "You're chatting with folks on an old-school BBS, not assisting customers. "
    "Sound like a regular South Alabama fella: plainspoken, a little dry, relaxed, "
    "occasionally funny. Don't perform a cartoon accent or overdo 'reckon' and 'howdy'. "
    "Skip generic praise, summaries, and scripted openings like 'Great question!' "
    "Don't end every message with a question; only ask when you actually want to know. "
    "Often just answer and leave it there. One short sentence is fine. "
    "Keep each entire answer under 200 characters, with a complete ending. "
    "No lists, markdown, emojis, or long speeches. "
    "When asked about 'today' or a date, use the date provided below. "
    "You have no live news or historical lookup tool: don't invent specific "
    "on-this-day events, dates, or current news. Say when you're unsure."
)


def current_instructions(now=None):
    """Use the BBS's local calendar date for date-sensitive chat."""
    now = now or datetime.now(ZoneInfo("America/Chicago"))
    return INSTRUCTIONS + "\n" + BUBBA_STYLE + "\nToday is " + now.strftime("%A, %B %d, %Y") + " (Central Time)."


def complete_reply(value, limit=MAX_REPLY_CHARS):
    """Avoid displaying a half-finished sentence if a model runs long."""
    value = clean(value)
    if len(value) <= limit:
        return value
    import re
    candidate = value[:limit]
    endings = list(re.finditer(r"[.!?](?=\s|$)", candidate))
    if endings:
        return candidate[:endings[-1].end()].strip()
    return "Well, I got carried away there. Ask me again?"



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


def broadcast_fields(message):
    """Mystic MRC clients render nick prefixes supplied inside message text.

    Keep ToUser empty for room broadcasts; ALL is not a valid public recipient
    for the Mystic 1.3.7 chat script.
    """
    formatted = "|03<|10" + BOT_NAME + "|03>|16|07 " + message
    return (BOT_NAME, BOT_SITE, ROOM, "", "", ROOM, formatted)


def is_conversation_message(message, active_until, now):
    """A mention starts a session; subsequent messages work until it expires."""
    return bool(MENTION.search(message)) or now < active_until


def main():
    host = os.environ.get("LOCAL_MRC_HOST", "").strip()
    port = int(os.environ.get("LOCAL_MRC_PORT", "5000"))
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("BUBBABOT_AI_MODEL", "gpt-4o-mini")
    if not host or not key:
        raise SystemExit("LOCAL_MRC_HOST and OPENAI_API_KEY are required")
    if not 1 <= port <= 65535:
        raise SystemExit("Invalid LOCAL_MRC_PORT")
    engine = BubbaEngine({ROOM}, cooldown_seconds=FOLLOWUP_COOLDOWN_SECONDS, max_replies_per_hour=20)
    histories = defaultdict(list)
    active_until = {}
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
                        sender_key = (site.casefold(), user.casefold())
                        now = time.monotonic()
                        mentioned = bool(MENTION.search(message))
                        if not is_conversation_message(message, active_until.get(sender_key, 0), now):
                            histories.pop(sender_key, None)
                            active_until.pop(sender_key, None)
                            continue
                        # The shared engine enforces rate limits and checks mentions.
                        # For an active session, prepend the bot name to satisfy its
                        # routing gate without changing the AI conversation text.
                        routing_message = message if mentioned else "Bubba " + message
                        packet = Packet(user, site, room.lstrip("#"), "ALL", "", room.lstrip("#"), routing_message)
                        allowed = engine.process(packet)
                        if allowed is None:
                            continue
                        if attempts >= 100:
                            print("Bubba request limit reached; restart required", flush=True)
                            continue
                        attempts += 1
                        history = histories[sender_key]
                        candidate = history + [{"role": "user", "content": message[:500]}]
                        try:
                            reply, usage = converse(candidate, api_key=key, model=model, instructions=current_instructions())
                        except Exception as exc:
                            print("AI request failed: " + type(exc).__name__, file=sys.stderr, flush=True)
                            continue
                        reply = complete_reply(reply)
                        if reply:
                            sock.sendall(encode(broadcast_fields(reply)).encode())
                            histories[sender_key] = (candidate + [{"role": "assistant", "content": reply}])[-MAX_HISTORY:]
                            active_until[sender_key] = time.monotonic() + SESSION_SECONDS
                    except (ValueError, UnicodeError) as exc:
                        print("Ignored malformed packet: " + type(exc).__name__, file=sys.stderr, flush=True)
        except (OSError, ConnectionError) as exc:
            print("Gateway connection lost: " + type(exc).__name__, file=sys.stderr, flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
