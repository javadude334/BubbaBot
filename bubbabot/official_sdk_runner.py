"""Approved MRC Mode 1 bot runner. Requires official SDK and credentials.

No fallback to legacy TCP, no arbitrary command-line TLS bypass.
"""
import os

from .bot_profile import BotProfile
from .official_sdk_adapter import wire_mode1_bot
from .sdk_bridge import SDKBridge


def build_bot():
    # Do not import or initialize the network SDK until configuration passes.
    token = os.environ.get("CONNECTOR_TOKEN", "")
    host = os.environ.get("CONNECTOR_HOST", "")
    slug = os.environ.get("BOT_SLUG", "")
    room = os.environ.get("BOT_ROOM", "bubba").lstrip("#")
    port = int(os.environ.get("CONNECTOR_PORT", "5010"))
    if not token or not host or not slug:
        raise ValueError("CONNECTOR_TOKEN, CONNECTOR_HOST, BOT_SLUG are required")
    if not 1 <= port <= 65535:
        raise ValueError("invalid connector port")
    if room.casefold() != "bubba":
        raise ValueError("BubbaBot may only join the approved room 'bubba'")
    from mrc_connector import MRCBot

    bot = MRCBot(host=host, port=port, token=token, slug=slug,
                 verify_tls=True, debug=False)
    bot.display_name = "Bubba"
    bridge = SDKBridge(BotProfile(name="Bubba", site=slug, room="bubba"))
    wire_mode1_bot(bot, bridge=bridge, expected_room="bubba")
    return bot


def main():
    build_bot().run()


if __name__ == "__main__":
    main()
