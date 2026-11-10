"""Offline room selection and simulated multi-user message routing.

Does not send JOIN commands or claim server-side room membership.
"""
from .bot_profile import BotProfile
from .engine import BubbaEngine
from .session import OfflineSession


class OfflineRoomManager:
    def __init__(self, profile: BotProfile, *, cooldown_seconds=0,
                 max_replies_per_hour=100, clock=None):
        self.profile = profile
        self.engine = BubbaEngine(
            {profile.room}, cooldown_seconds=cooldown_seconds,
            max_replies_per_hour=max_replies_per_hour, clock=clock
        )
        self.session = OfflineSession(
            self.engine, bot_name=profile.name, bot_site=profile.site
        )

    def handle_line(self, line: str) -> str | None:
        return self.session.handle_line(line)
