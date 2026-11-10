"""Offline, deterministic Bubba personality and command responses.

No network calls, credentials, or MRC transport dependencies.
"""
from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class Personality:
    name: str = "Bubba"
    room: str = "bubba"
    description: str = "A friendly, slightly goofy Southern regular on Dave's BBS."

    def respond(self, user: str, message: str) -> str | None:
        """Return a canned response for a recognized command, or None for AI routing."""
        if not isinstance(user, str) or not isinstance(message, str):
            return None
        user = user.strip()[:40] or "friend"
        command = message.strip().split(maxsplit=1)[0].casefold() if message.strip() else ""
        if command == ".help":
            return "Howdy! Try .help, .about, .status, or .joke. Or say Bubba to chat!"
        if command == ".about":
            return "I'm Bubba, Dave's BBS chat buddy. I hang out in #bubba, never #lobby."
        if command == ".status":
            return "Bubba's awake and running. AI chat may be unavailable; my old-fashioned replies still work."
        if command == ".joke":
            jokes = (
                "Why'd the computer go to the doctor? It caught a virus!",
                "I told my modem a joke, but it just kept dialing it in.",
                "My BBS is so old, even the electrons have gray hair.",
            )
            digest = hashlib.sha256((user.casefold() + ":" + message.strip().casefold()).encode("utf-8")).digest()
            return jokes[int.from_bytes(digest[:4], "big") % len(jokes)]
        return None
