"""On-demand, short-lived college football schedule facts; no sports database.

ESPN's public site endpoint is undocumented and may change. Fail closed.
"""
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TEAM_SLUGS = {
    "troy": "troy",
    "south alabama": "south-alabama",
    "alabama": "alabama",
    "auburn": "auburn",
}
TEAM_PATTERN = re.compile(r"\b(south alabama|jaguars|troy|trojans|crimson tide|alabama|auburn|war eagle)\b", re.I)
SPORTS_PATTERN = re.compile(r"\b(football|game|games|score|scores|schedule|playing|play|plays|played|opponent|weekend|tonight|tomorrow|saturday|sunday|next|last|won|lost|season|record|belt)\b", re.I)
URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{}/schedule?season={}"
CACHE_SECONDS = 1200
_cache = {}


def mentioned_teams(message):
    """Only request facts for teams named in an actual football question."""
    if not TEAM_PATTERN.search(message) or not SPORTS_PATTERN.search(message):
        return []
    found = []
    for match in TEAM_PATTERN.finditer(message):
        name = match.group().lower()
        slug = ("south alabama" if name in ("jaguars", "south alabama")
                else "troy" if name in ("trojans", "troy")
                else "alabama" if name in ("crimson tide", "alabama")
                else "auburn")
        if slug not in found:
            found.append(slug)
    return found[:3]


def _schedule(slug, season, *, transport=None, clock=None):
    clock = clock or time.monotonic
    key = (slug, season)
    now = clock()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]
    request = urllib.request.Request(
        URL.format(TEAM_SLUGS[slug], season),
        headers={"User-Agent": "BubbaBot/1.0 (BBS sports schedule)", "Accept": "application/json"},
    )
    try:
        with (transport or urllib.request.urlopen)(request, timeout=5) as response:
            data = json.load(response)
        events = data.get("events", [])
        if not isinstance(events, list):
            return None
        _cache[key] = (now, events)
        return events
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, KeyError):
        return None


def sports_context(message, *, now=None, transport=None, clock=None):
    teams = mentioned_teams(message)
    if not teams:
        return ""
    now = now or datetime.now(ZoneInfo("America/Chicago"))
    snippets = []
    for slug in teams:
        events = _schedule(slug, now.year, transport=transport, clock=clock)
        if events is None:
            continue
        games = []
        for event in events:
            try:
                kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/Chicago"))
                competitors = event["competitions"][0]["competitors"]
                if len(competitors) != 2:
                    continue
                labels = [c["team"]["displayName"] for c in competitors]
                raw_status = event.get("status") or {}
                status = (raw_status.get("type") or {}).get("state")
                if not status and kickoff > now:
                    status = "pre"
                if status not in ("pre", "in", "post"):
                    continue
                scores = [str(c.get("score", "?")) for c in competitors]
                detail = f"{kickoff:%a %b %d %I:%M %p} CT: {labels[0]} vs {labels[1]} ({status})"
                if status in ("in", "post") and all(s.isdigit() for s in scores):
                    detail += f"; score {labels[0]} {scores[0]}, {labels[1]} {scores[1]}"
                games.append((kickoff, detail))
            except (KeyError, IndexError, TypeError, ValueError, AttributeError):
                continue
        # Weekend questions must not include games from later weeks.
        if re.search(r"\b(weekend|saturday|sunday)\b", message, re.I):
            from datetime import timedelta
            saturday = (now + timedelta(days=(5 - now.weekday()) % 7)).date()
            sunday = saturday + timedelta(days=1)
            chosen = sorted(g for g in games if saturday <= g[0].date() <= sunday)
        else:
            past = sorted((g for g in games if g[0] <= now), reverse=True)
            future = sorted(g for g in games if g[0] > now)
            chosen = past[:1] + future[:2]
        if chosen:
            snippets.append(slug.title() + ": " + " | ".join(g[1] for g in chosen))
    if not snippets:
        return ("SPORTS LOOKUP: No verified game found for the requested time, or schedule unavailable. "
                "Do not claim any specific opponent, date, result, or score.")
    return ("VERIFIED SPORTS DATA (ESPN schedule, retrieved now; Central Time). "
            "Use ONLY these facts for current matchups/scores. A pre game has NOT happened yet. "
            "If asked for a different game, say it isn't verified. "
            + "\n".join(snippets))
