"""On-demand, short-lived college football schedule facts; no sports database.

ESPN's public site endpoint is undocumented and may change. Fail closed.
"""
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
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
    # ESPN currently rejects BubbaBot's custom User-Agent with HTTP 403.
    # Use the default urllib request, which has been verified against the live endpoint.
    request = URL.format(TEAM_SLUGS[slug], season)
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



def _team_key(message):
    """Prefer a named team, preserving 'South Alabama' over 'Alabama'."""
    found = TEAM_PATTERN.search(message)
    if not found:
        return None
    name = found.group().lower()
    if name in ("south alabama", "jaguars"):
        return "south alabama"
    if name in ("troy", "trojans"):
        return "troy"
    if name in ("alabama", "crimson tide"):
        return "alabama"
    return "auburn"


def _games(team, now, transport=None, clock=None):
    events = _schedule(team, now.year, transport=transport, clock=clock)
    if events is None:
        return None
    games = []
    for event in events:
        try:
            kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(now.tzinfo)
            competition = event["competitions"][0]
            competitors = competition["competitors"]
            if len(competitors) != 2:
                continue
            own = next((c for c in competitors if
                        TEAM_SLUGS[team].replace("-", " ") in
                        (c["team"].get("location", "") + " " + c["team"].get("displayName", "")).lower()), None)
            # Use the schedule's actual team ID when available; name is a fallback.
            if own is None:
                own = next((c for c in competitors if
                            team == "troy" and c["team"].get("id") == "2653" or
                            team == "alabama" and c["team"].get("id") == "333"), None)
            if own is None:
                continue
            opponent = next(c for c in competitors if c is not own)
            raw_status = event.get("status") or competition.get("status") or {}
            status_type = raw_status.get("type") or {}
            state = status_type.get("state")
            completed = bool(status_type.get("completed"))
            if not state:
                state = "pre" if kickoff > now else "unknown"
            score_own = own.get("score")
            score_other = opponent.get("score")
            if isinstance(score_own, dict):
                score_own = score_own.get("value")
            if isinstance(score_other, dict):
                score_other = score_other.get("value")
            venue = competition.get("venue") or {}
            address = venue.get("address") or {}
            games.append({
                "date": kickoff, "opponent": opponent["team"]["displayName"],
                "opponent_location": opponent["team"].get("location", ""),
                "home_away": own.get("homeAway", ""),
                "neutral": bool(competition.get("neutralSite")),
                "city": address.get("city", ""),
                "state": state, "completed": completed or state == "post",
                "scores": (score_own, score_other),
            })
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            continue
    return sorted(games, key=lambda g: g["date"])


def _short_name(name):
    for full, short in (("Troy Trojans", "Troy"), ("South Alabama Jaguars", "South Alabama"),
                        ("Georgia Southern Eagles", "Georgia Southern"),
                        ("Arkansas State Red Wolves", "Arkansas State"),
                        ("Alabama Crimson Tide", "Alabama")):
        if name == full:
            return short
    return name


def _sports_intent(message, history):
    """Resolve team and intent using only the same visitor's prior user turns."""
    team = _team_key(message)
    previous = []
    for entry in reversed(history or []):
        if entry.get("role") == "user":
            previous.append(entry.get("content", ""))
    last_team = next((_team_key(m) for m in previous if _team_key(m)), None)
    prior_sports = any(SPORTS_PATTERN.search(m) for m in previous[:3])
    followup = bool(re.search(
        r"\b(after that|afterwards|then|next game|next week|how about|what about|"
        r"when do they|who do they|who are they|what time|where|score)\b", message, re.I))
    if not team and followup and prior_sports:
        team = last_team
    if team and not SPORTS_PATTERN.search(message):
        if not (followup and prior_sports):
            team = None
    return team


def sports_reply(message, *, history=None, now=None, transport=None, clock=None):
    """Return a verified, short conversational sports answer, or None for small talk.

    Never route a recognized sports question through free-form AI: the schedule
    is authoritative and the bot must not improvise opponents or results.
    """
    now = now or datetime.now(ZoneInfo("America/Chicago"))
    team = _sports_intent(message, history)
    if not team:
        return None
    games = _games(team, now, transport=transport, clock=clock)
    if games is None or not games:
        return "I can't check the schedule right now, so I won't guess."
    future = [g for g in games if g["date"] > now]
    past = [g for g in games if g["date"] <= now]
    msg = message.lower()
    chosen = None
    # Explicit opponent: match any game in the schedule, not just the next two.
    for g in games:
        opponent = g["opponent"].lower()
        short = _short_name(g["opponent"]).lower()
        if short in msg or opponent in msg:
            chosen = g
            break
    if chosen is None and re.search(r"\b(after that|afterwards|who do they play after|who's next)\b", msg):
        # The previous user question determines which game "that" refers to.
        anchor = None
        for entry in reversed(history or []):
            if entry.get("role") != "user":
                continue
            previous_msg = entry.get("content", "")
            if _team_key(previous_msg) or SPORTS_PATTERN.search(previous_msg):
                if re.search(r"\b(weekend|saturday|sunday)\b", previous_msg, re.I):
                    saturday = (now + timedelta(days=(5 - now.weekday()) % 7)).date()
                    anchor = next((g for g in games if saturday <= g["date"].date() <= saturday + timedelta(days=1)), None)
                elif re.search(r"\b(next|playing|play)\b", previous_msg, re.I):
                    anchor = future[0] if future else None
                if anchor:
                    break
        chosen = next((g for g in games if anchor and g["date"] > anchor["date"]), None)
        if chosen is None and not anchor:
            chosen = future[1] if len(future) > 1 else None
    elif chosen is None and re.search(r"\b(weekend|saturday|sunday)\b", msg):
        saturday = (now + timedelta(days=(5 - now.weekday()) % 7)).date()
        chosen = next((g for g in games if saturday <= g["date"].date() <= saturday + timedelta(days=1)), None)
    elif chosen is None and re.search(r"\b(score|won|lost|last game|last week)\b", msg):
        # A bare score question normally refers to the current/next game.
        # Do not substitute an unrelated previous opponent when no final exists.
        if re.search(r"\b(last game|last week)\b", msg):
            chosen = past[-1] if past else None
        else:
            chosen = future[0] if future else (past[-1] if past else None)
    elif chosen is None:
        chosen = future[0] if future else None
    if chosen is None:
        return "I couldn't find that game on the verified schedule."
    opponent = _short_name(chosen["opponent"])
    subject = "Troy" if team == "troy" else "Alabama" if team == "alabama" else _short_name(team.title())
    date = chosen["date"]
    if re.search(r"\b(score|won|lost|result)\b", msg):
        a, b = chosen["scores"]
        if chosen["completed"] and a is not None and b is not None:
            return f"{subject} {a}, {opponent} {b}. That's the final."
        return f"I don't have a verified final score for {subject} against {opponent}."
    if chosen["neutral"]:
        answer = f"{subject}'s got {opponent} at a neutral site"
    elif chosen["home_away"] == "away":
        destination = chosen["city"] or chosen["opponent_location"]
        answer = f"{subject}'s gotta head to {destination} to play {opponent}" if destination else f"{subject}'s on the road against {opponent}"
    elif chosen["home_away"] == "home":
        answer = f"{subject}'s got {opponent} comin' to town"
    else:
        answer = f"{subject}'s playing {opponent}"
    if re.search(r"\b(when|date|what day|which day|weekend|saturday|sunday|after that|afterwards)\b", msg):
        answer += f" on {date:%A, %B} {date.day}"
    if re.search(r"\b(what time|kickoff|time does|when exactly)\b", msg):
        answer += f" at {date:%I:%M %p} Central"
    return answer + "."

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
            chosen = past[:1] + future[:4]
        if chosen:
            snippets.append(slug.title() + ": " + " | ".join(g[1] for g in chosen))
    if not snippets:
        return ("SPORTS LOOKUP: No verified game found for the requested time, or schedule unavailable. "
                "Do not claim any specific opponent, date, result, or score.")
    return ("VERIFIED SPORTS DATA (ESPN schedule, retrieved now; Central Time). "
            "Use ONLY these facts for current matchups/scores. A pre game has NOT happened yet. "
            "If asked for a different game, say it isn't verified. "
            + "\n".join(snippets))
