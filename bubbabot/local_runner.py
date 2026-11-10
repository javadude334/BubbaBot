"""Local-only command-line MRC simulator client with rotating logs."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .reconnecting_runner import run_reconnecting
from .bot_profile import BotProfile
from .room_manager import OfflineRoomManager
from .mrc_client_session import LocalMRCSession
from .mrc_handshake import ClientIdentity
from .settings import load_settings
from .transport import LocalTCPTransport


def main(argv=None):
    parser = argparse.ArgumentParser(description="BubbaBot local-only TCP test client")
    parser.add_argument("--config", default="bubba.local.json")
    parser.add_argument("--max-messages", type=int, default=100)
    parser.add_argument("--max-sessions", type=int, default=1,
                        help="Maximum local connections including reconnects (default 1)")
    args = parser.parse_args(argv)
    settings = load_settings(args.config)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("bubbabot")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_dir / "bubbabot.log", maxBytes=500_000,
                                  backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.info("Starting local-only test client (no AI API)")
    print("BubbaBot LOCAL TEST ONLY; no public MRC connection or AI API.", flush=True)
    profile = BotProfile(name=settings.bot_name, site=settings.site, room=settings.room)
    print(f"Connecting to {settings.host}:{settings.port} as {profile.name} ({profile.site}) in #{profile.room}", flush=True)
    try:
        room_manager = OfflineRoomManager(profile,
                                          cooldown_seconds=settings.cooldown_seconds,
                                          max_replies_per_hour=settings.max_replies_per_hour)
        session = room_manager.session
        def make_session():
            return LocalMRCSession(
                LocalTCPTransport(host=settings.host, port=settings.port,
                                  timeout=3, max_attempts=1),
                ClientIdentity(site=settings.site), session,
                max_messages=args.max_messages
            )

        result = run_reconnecting(make_session, max_sessions=args.max_sessions,
                                  logger=logger)
        logger.info("Complete sessions=%s messages=%s replies=%s",
                    result["sessions"], result["messages"], result["replies"])
        print(f"Complete: {result['sessions']} sessions, "
              f"{result['messages']} messages, {result['replies']} replies")
    except (ConnectionError, OSError, ValueError, UnicodeError) as exc:
        logger.error("Local session failed: %s", type(exc).__name__)
        parser.exit(1, f"Local test failed: {exc}\n")
    finally:
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    main()
