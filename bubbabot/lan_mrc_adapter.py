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
from .visitor_facts import extract_safe_facts, memory_command, memory_context, normalize_mrc_message

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


def memory_command_reply(command, memory, site, user):
    """Handle local memory commands without an AI call; never claim failed deletion."""
    if command not in ("recall", "forget"):
        return None
    if memory is None:
        return "My memory isn't available right now."
    try:
        if command == "forget":
            memory.forget(site, user)
            return "Done. I cleared what I remembered about you."
        notes = memory.recall(site, user)
        return complete_reply("I remember: " + "; ".join(notes)) if notes else "I don't have any saved facts about you."
    except Exception as exc:
        print("Memory command failed: " + type(exc).__name__, file=sys.stderr, flush=True)
        return "My memory isn't available right now. Try again later."


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
    last_memory_command = {}
    attempts = 0
    memory = None
    secret = os.environ.get("BUBBABOT_MEMORY_HMAC_KEY", "").strip()
    if secret:
        try:
            from .postgres_memory import PostgresVisitorMemory
            memory = PostgresVisitorMemory(secret=bytes.fromhex(secret))
            memory.initialize()
            print("PostgreSQL visitor memory enabled", flush=True)
        except Exception as exc:
            memory = None
            print("PostgreSQL memory unavailable: " + type(exc).__name__, file=sys.stderr, flush=True)
    else:
        print("PostgreSQL memory disabled: BUBBABOT_MEMORY_HMAC_KEY not configured", flush=True)
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
                        message = normalize_mrc_message(message, user)
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
                        # Commands are local and must not wait for AI or its
                        # five-second cooldown. Limit repeat commands per visitor.
                        command = memory_command(message)
                        if command:
                            if now - last_memory_command.get(sender_key, -1000) < 2:
                                continue
                            last_memory_command[sender_key] = now
                            reply = memory_command_reply(command, memory, site, user)
                            if command == "forget" and reply.startswith("Done."):
                                histories.pop(sender_key, None)
                            sock.sendall(encode(broadcast_fields(reply)).encode())
                            active_until[sender_key] = time.monotonic() + SESSION_SECONDS
                            continue
                        # Save allowlisted facts even when ordinary chat is on
                        # cooldown or the AI request fails.
                        if memory is not None:
                            facts = extract_safe_facts(message)
                            for fact in facts:
                                try:
                                    memory.remember_screened(site, user, fact)
                                except Exception as exc:
                                    print("Memory write failed: " + type(exc).__name__, file=sys.stderr, flush=True)
                        # The shared engine enforces limits for AI replies only.
                        routing_message = message if mentioned else "Bubba " + message
                        packet = Packet(user, site, room.lstrip("#"), "ALL", "", room.lstrip("#"), routing_message)
                        allowed = engine.process(packet)
                        if allowed is None:
                            continue
                        if attempts >= 100:
                            print("Bubba request limit reached; restart required", flush=True)
                            continue
                        attempts += 1
                        notes = []
                        if memory is not None:
                            try:
                                notes = memory.recall(site, user)
                            except Exception as exc:
                                print("Memory read failed: " + type(exc).__name__, file=sys.stderr, flush=True)
                        history = histories[sender_key]
                        candidate = history + [{"role": "user", "content": message[:500]}]
                        try:
                            reply, usage = converse(candidate, api_key=key, model=model,
                                instructions=current_instructions() + memory_context(notes))
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
