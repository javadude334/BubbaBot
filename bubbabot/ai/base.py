"""Common AI request and response types."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


class AIError(Exception):
    """Provider failure with a normalized category."""

    def __init__(self, category: str, message: str = ""):
        super().__init__(message or category)
        self.category = category


class AIProvider(Protocol):
    def generate(self, messages: list[dict[str, str]]) -> AIResponse: ...
