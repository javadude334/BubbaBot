"""Shared AI conversation handling for LAN and official MRC adapters."""
import os
import sys
import time
from collections import defaultdict

from .chat import converse
from .engine import BubbaEngine
from .protocol import Packet
from .routing import MENTION
from .sports import sports_context, sports_reply
from .visitor_facts import extract_safe_facts, memory_command, memory_context, normalize_mrc_message
from .lan_mrc_adapter import (
    MAX_HISTORY, SESSION_SECONDS, FOLLOWUP_COOLDOWN_SECONDS,
    complete_reply, current_instructions, is_conversation_message, memory_command_reply,
)


class ConversationService:
    """Per-process conversations; memory is keyed by BBS and handle."""

    def __init__(self, *, room="bubba", api_key, model="gpt-4o-mini",
                 memory=None, max_requests=100, clock=None, responder=None):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for AI mode")
        self.room = room.lstrip("#").casefold()
        if self.room != "bubba":
            raise ValueError("Only the approved bubba room is supported")
        self.api_key = api_key
        self.model = model
        self.memory = memory
        self.clock = clock or time.monotonic
        self.responder = responder or converse
        self.engine = BubbaEngine({self.room}, cooldown_seconds=FOLLOWUP_COOLDOWN_SECONDS,
                                  max_replies_per_hour=20, clock=self.clock)
        self.histories = defaultdict(list)
        self.active_until = {}
        self.last_memory_command = {}
        self.attempts = 0
        self.max_requests = max_requests

    def handle(self, user, site, room, text):
        room = room.lstrip("#").casefold()
        if room != self.room or not user or not site:
            return None
        if user.casefold() in ("bubba", "bubbabot", "server", "client"):
            return None
        message = normalize_mrc_message(text, user)
        if not message or len(message) > 500:
            return None
        key = (site.casefold(), user.casefold())
        now = self.clock()
        mentioned = bool(MENTION.search(message))
        if not is_conversation_message(message, self.active_until.get(key, 0), now):
            self.histories.pop(key, None)
            self.active_until.pop(key, None)
            return None
        command = memory_command(message)
        if command:
            if now - self.last_memory_command.get(key, -1000) < 2:
                return None
            self.last_memory_command[key] = now
            reply = memory_command_reply(command, self.memory, site, user)
            if command == "forget" and reply.startswith("Done."):
                self.histories.pop(key, None)
            self.active_until[key] = self.clock() + SESSION_SECONDS
            return reply
        if self.memory is not None:
            for fact in extract_safe_facts(message):
                try:
                    self.memory.remember_screened(site, user, fact)
                except Exception as exc:
                    print("Memory write failed: " + type(exc).__name__, file=sys.stderr, flush=True)
        routing = message if mentioned else "Bubba " + message
        packet = Packet(user, site, room, "ALL", "", room, routing)
        if self.engine.process(packet) is None:
            return None
        if self.attempts >= self.max_requests:
            print("Bubba request limit reached; restart required", flush=True)
            return None
        self.attempts += 1
        notes = []
        if self.memory is not None:
            try:
                notes = self.memory.recall(site, user)
            except Exception as exc:
                print("Memory read failed: " + type(exc).__name__, file=sys.stderr, flush=True)
        history = self.histories[key]
        candidate = history + [{"role": "user", "content": message[:500]}]
        grounded = sports_reply(message, history=history)
        if grounded is not None:
            reply = complete_reply(grounded)
        else:
            instructions = current_instructions() + memory_context(notes)
            verified = sports_context(message)
            if verified:
                instructions += "\n" + verified
            try:
                result, _usage = self.responder(candidate, api_key=self.api_key,
                                                 model=self.model, instructions=instructions)
            except Exception as exc:
                print("AI request failed: " + type(exc).__name__, file=sys.stderr, flush=True)
                return None
            reply = complete_reply(result)
        if reply:
            self.histories[key] = (candidate + [{"role": "assistant", "content": reply}])[-MAX_HISTORY:]
            self.active_until[key] = self.clock() + SESSION_SECONDS
        return reply or None


def memory_from_environment():
    secret = os.environ.get("BUBBABOT_MEMORY_HMAC_KEY", "").strip()
    if not secret:
        print("PostgreSQL memory disabled: key not configured", flush=True)
        return None
    try:
        from .postgres_memory import PostgresVisitorMemory
        memory = PostgresVisitorMemory(secret=bytes.fromhex(secret))
        memory.initialize()
        print("PostgreSQL visitor memory enabled", flush=True)
        return memory
    except Exception as exc:
        print("PostgreSQL memory unavailable: " + type(exc).__name__, file=sys.stderr, flush=True)
        return None
