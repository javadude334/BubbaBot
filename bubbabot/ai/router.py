"""Cloud-first AI router with local fallback.

A conservative estimate is reserved BEFORE cloud calls, and is charged even
on uncertain outcomes; this prevents unaccounted retries. This is a
single-process budget guard, not a provider-enforced billing limit.
"""
from decimal import Decimal

from .base import AIError, AIResponse


class AIRouter:
    def __init__(self, primary, fallback, budget, estimated_call_usd="0.01"):
        self.primary = primary
        self.fallback = fallback
        self.budget = budget
        self.estimate = Decimal(estimated_call_usd)
        if self.estimate <= 0:
            raise ValueError("estimated_call_usd must be positive")
        self.cloud_disabled = False

    def generate(self, messages: list[dict[str, str]]) -> AIResponse:
        if not self.cloud_disabled and self.budget.can_spend(self.estimate):
            # Charge before sending; a timed-out request may still be billed.
            self.budget.charge(self.estimate)
            try:
                return self.primary.generate(messages)
            except AIError as exc:
                if exc.category in ("quota", "auth"):
                    self.cloud_disabled = True
                elif exc.category not in ("rate_limit", "timeout", "unavailable"):
                    raise
        return self.fallback.generate(messages)
