"""Conservative gate for proposed long-term memory notes.

This filter is deliberately fail-closed. It is NOT a guarantee that all
personally identifying information can be recognized. Use with an additional
review/classification layer before automatic memory is enabled.
"""
import re

SAFE_TOPICS = {
    "fishing", "gardening", "country music", "rock music", "jazz",
    "reading", "cooking", "hiking", "camping", "woodworking",
    "baseball", "football", "dogs", "cats", "video games",
}
SENSITIVE = re.compile(
    r"\b(?:address|street|road|avenue|boulevard|zip|postcode|phone|email|"
    r"birthday|birthdate|born|ssn|social security|password|token|"
    r"account|bank|credit card|diagnosis|medication|hospital|"
    r"employer|workplace|salary|income|political|religion)\b",
    re.IGNORECASE,
)
IDENTIFIERS = re.compile(
    r"@|https?://|\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{5}(?:-\d{4})?\b|"
    r"\b\d{1,4}\s+\w+\s+(?:st|street|rd|road|ave|avenue)\b",
    re.IGNORECASE,
)


def screen_memory_note(note: str) -> str | None:
    """Allow only exact, pre-approved interest statements; otherwise reject.

    Future automatic extraction must map chat text to a fixed allowed
    category without carrying over visitor-supplied text or identifiers.
    """
    if not isinstance(note, str):
        return None
    normalized = " ".join(note.strip().casefold().split())
    if len(normalized) > 80 or SENSITIVE.search(normalized) or IDENTIFIERS.search(normalized):
        return None
    if normalized.startswith("enjoys "):
        topic = normalized[len("enjoys "):]
        if topic in SAFE_TOPICS:
            return "Enjoys " + topic
    return None
