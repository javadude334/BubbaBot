"""Adapter from the official MRC Mode 1 SDK to Bubba's policy engine.

The SDK owns TLS, authentication, heartbeat and reconnection. This module
never supplies tokens, guesses room names, or bypasses TLS verification.
"""
from .sdk_bridge import IncomingChat, SDKBridge


def wire_mode1_bot(bot, bridge=None, *, expected_room="bubba"):
    """Register the documented on_message callback on an MRCBot instance.

    The SDK sets bot.room after AUTH_OK. Fail closed if that room has not
    been established, is lobby, or is different from the approved room.
    """
    bridge = bridge if bridge is not None else SDKBridge()
    expected = expected_room.lstrip("#").casefold()
    if not expected or expected == "lobby":
        raise ValueError("dedicated non-lobby room required")
    if bridge.profile.room.casefold() != expected:
        raise ValueError("bridge must be configured for approved room")

    @bot.on_message
    def receive(from_user, from_bbs, text, session_id=None):
        room = str(getattr(bot, "room", "") or "").lstrip("#")
        if room.casefold() != expected:
            return
        outgoing = bridge.handle(IncomingChat(
            user=from_user, site=from_bbs, room=room, text=text
        ))
        if outgoing is not None:
            # Mode 1: SDK sends SAY only to the assigned room.
            bot.say(outgoing.text)

    return receive
