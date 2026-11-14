"""Persistent fictional Possum Creek events. No personal chat logs are stored.

This module is deliberately separate from visitor memory. Call record_event only
for explicitly fictional-world material, never for unverified real-world allegations.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class WorldMemory:
    def __init__(self, path):
        self.path = str(path)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS world_characters (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    description TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS world_relationships (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL REFERENCES world_characters(id),
                    related_id INTEGER NOT NULL REFERENCES world_characters(id),
                    relation TEXT NOT NULL,
                    UNIQUE(character_id, related_id, relation)
                );
                CREATE TABLE IF NOT EXISTS world_events (
                    id INTEGER PRIMARY KEY,
                    fingerprint TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'normal',
                    status TEXT NOT NULL DEFAULT 'developing',
                    provenance TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_event_characters (
                    event_id INTEGER NOT NULL REFERENCES world_events(id),
                    character_id INTEGER NOT NULL REFERENCES world_characters(id),
                    PRIMARY KEY(event_id, character_id)
                );
                CREATE TABLE IF NOT EXISTS world_event_updates (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES world_events(id),
                    summary TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(event_id, summary)
                );
                CREATE TABLE IF NOT EXISTS visitor_event_knowledge (
                    site TEXT NOT NULL,
                    handle TEXT NOT NULL,
                    update_id INTEGER NOT NULL REFERENCES world_event_updates(id),
                    delivered_at TEXT NOT NULL,
                    PRIMARY KEY(site, handle, update_id)
                );
                CREATE TABLE IF NOT EXISTS story_scheduler_state (
                    name TEXT PRIMARY KEY,
                    last_run_at TEXT,
                    paused INTEGER NOT NULL DEFAULT 0
                );
            """)

    @staticmethod
    def timestamp():
        return datetime.now(timezone.utc).isoformat()

    def record_event(self, *, kind, summary, characters=(), severity="normal",
                     provenance="fictional_user_report", occurred_at=None):
        if provenance not in ("fictional_user_report", "fictional_seed"):
            raise ValueError("Only explicitly fictional events may be recorded")
        if not summary.strip() or len(summary) > 500:
            raise ValueError("Invalid summary")
        if severity not in ("normal", "important", "critical"):
            raise ValueError("Invalid severity")
        names = sorted({name.strip() for name in characters if name.strip()})
        if any(len(name) > 80 for name in names):
            raise ValueError("Character name too long")
        canonical = json.dumps([kind.strip().casefold(), summary.strip().casefold(),
                                [n.casefold() for n in names]], ensure_ascii=True)
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        now = self.timestamp()
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO world_events
                (fingerprint, kind, summary, severity, status, provenance,
                 occurred_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'developing', ?, ?, ?, ?)""",
                (fingerprint, kind, summary.strip(), severity, provenance,
                 occurred_at or now, now, now))
            event_id = db.execute("SELECT id FROM world_events WHERE fingerprint=?",
                                  (fingerprint,)).fetchone()["id"]
            for name in names:
                db.execute("INSERT OR IGNORE INTO world_characters(name) VALUES (?)", (name,))
                character_id = db.execute(
                    "SELECT id FROM world_characters WHERE name=? COLLATE NOCASE",
                    (name,)).fetchone()["id"]
                db.execute("""INSERT OR IGNORE INTO world_event_characters
                    (event_id, character_id) VALUES (?, ?)""", (event_id, character_id))
            return event_id

    def add_update(self, event_id, summary, *, provenance="fictional_story_engine",
                   status=None):
        if provenance not in ("fictional_story_engine", "fictional_user_report"):
            raise ValueError("Invalid provenance")
        if not summary.strip() or len(summary) > 500:
            raise ValueError("Invalid update")
        if status is not None and status not in ("developing", "resolved"):
            raise ValueError("Invalid status")
        now = self.timestamp()
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO world_event_updates
                (event_id, summary, provenance, created_at) VALUES (?, ?, ?, ?)""",
                (event_id, summary.strip(), provenance, now))
            if status is not None:
                db.execute("UPDATE world_events SET status=?, updated_at=? WHERE id=?",
                           (status, now, event_id))
            return db.execute("""SELECT id FROM world_event_updates
                WHERE event_id=? AND summary=?""",
                (event_id, summary.strip())).fetchone()["id"]

    def unseen_updates(self, site, handle, limit=3):
        with self.connect() as db:
            rows = db.execute("""SELECT u.id, u.event_id, u.summary, e.severity
                FROM world_event_updates u JOIN world_events e ON e.id=u.event_id
                LEFT JOIN visitor_event_knowledge k ON k.update_id=u.id
                    AND k.site=? AND k.handle=?
                WHERE k.update_id IS NULL
                ORDER BY u.id DESC LIMIT ?""",
                (site.casefold(), handle.casefold(), max(0, min(limit, 10)))).fetchall()
            return [dict(row) for row in rows]

    def mark_delivered(self, site, handle, update_id):
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO visitor_event_knowledge
                (site, handle, update_id, delivered_at) VALUES (?, ?, ?, ?)""",
                (site.casefold(), handle.casefold(), update_id, self.timestamp()))

    def event(self, event_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM world_events WHERE id=?", (event_id,)).fetchone()
            return dict(row) if row else None
