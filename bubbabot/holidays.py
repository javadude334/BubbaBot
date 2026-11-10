"""Offline US holiday calendar for Bubba's conversational context."""
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from datetime import datetime


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    next_month = date(year + (month == 12), month % 12 + 1, 1)
    last = next_month - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def easter(year: int) -> date:
    """Gregorian Easter Sunday (Meeus/Jones/Butcher algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def holidays(year: int) -> dict[date, list[str]]:
    entries = [
        (date(year, 1, 1), "New Year's Day"),
        (nth_weekday(year, 1, 0, 3), "Martin Luther King Jr. Day"),
        (date(year, 2, 14), "Valentine's Day"),
        (nth_weekday(year, 2, 0, 3), "Presidents' Day"),
        (date(year, 3, 17), "St. Patrick's Day"),
        (easter(year), "Easter Sunday"),
        (last_weekday(year, 5, 0), "Memorial Day"),
        (date(year, 6, 19), "Juneteenth"),
        (date(year, 7, 4), "Independence Day"),
        (nth_weekday(year, 9, 0, 1), "Labor Day"),
        (date(year, 9, 19), "Talk Like a Pirate Day"),
        (date(year, 9, 29), "National Coffee Day"),
        (date(year, 10, 31), "Halloween"),
        (date(year, 11, 11), "Veterans Day"),
        (nth_weekday(year, 11, 3, 4), "Thanksgiving"),
        (date(year, 12, 25), "Christmas Day"),
        (date(year, 12, 31), "New Year's Eve"),
    ]
    result: dict[date, list[str]] = {}
    for day, name in entries:
        result.setdefault(day, []).append(name)
    return result


def holiday_context(today: date | None = None, timezone: str = "America/Chicago") -> str:
    """Compact context to add to the shared personality prompt, no API needed."""
    if today is None:
        today = datetime.now(ZoneInfo(timezone)).date()
    current = holidays(today.year)
    upcoming = [(day, name) for year in (today.year, today.year + 1)
                for day, names in holidays(year).items()
                for name in names if day >= today]
    next_day, next_name = min(upcoming, key=lambda item: item[0])
    todays = ", ".join(current.get(today, [])) or "No listed holiday"
    return (f"Local date: {today.isoformat()} ({timezone}). "
            f"Today: {todays}. Next holiday: {next_name} in {(next_day - today).days} day(s). "
            "Mention holidays naturally when relevant; do not force holiday greetings.")
