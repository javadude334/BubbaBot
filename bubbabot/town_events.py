"""Persistent, shared fictional town events. No network or AI calls.

Requires psycopg, already used by visitor memory. Event IDs are idempotency keys;
events are never silently overwritten. Status changes preserve an audit trail.
"""
import json
import psycopg

SCHEMA = """
CREATE TABLE IF NOT EXISTS town_events (
 event_id text PRIMARY KEY,
 title text NOT NULL,
 location text NOT NULL DEFAULT '',
 event_time timestamptz,
 status text NOT NULL CHECK (status IN ('planned','ongoing','completed','cancelled')),
 details jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS town_event_history (
 history_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 event_id text NOT NULL REFERENCES town_events(event_id),
 occurred_at timestamptz NOT NULL DEFAULT now(),
 action text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS town_events_time_idx ON town_events(event_time);
"""

class TownEvents:
    def __init__(self, dsn="dbname=bubbabot user=bubbabot"):
        self.dsn = dsn

    def initialize(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute(SCHEMA)

    def create(self, event_id, title, *, location="", event_time=None,
               status="planned", details=None):
        if not event_id or not title or status not in {"planned","ongoing","completed","cancelled"}:
            raise ValueError("invalid event")
        details = details or {}
        with psycopg.connect(self.dsn) as conn:
            with conn.transaction():
                inserted = conn.execute(
                    """INSERT INTO town_events(event_id,title,location,event_time,status,details)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                    ON CONFLICT(event_id) DO NOTHING RETURNING event_id""",
                    (event_id,title,location,event_time,status,json.dumps(details))
                ).fetchone()
                if inserted:
                    conn.execute(
                        "INSERT INTO town_event_history(event_id,action,details) VALUES (%s,%s,%s::jsonb)",
                        (event_id,"created",json.dumps({"status":status})))
                return bool(inserted)

    def transition(self, event_id, status, *, note=""):
        if status not in {"planned","ongoing","completed","cancelled"}:
            raise ValueError("invalid status")
        with psycopg.connect(self.dsn) as conn:
            with conn.transaction():
                row = conn.execute(
                    "SELECT status FROM town_events WHERE event_id=%s FOR UPDATE",
                    (event_id,)).fetchone()
                if row is None:
                    raise KeyError(event_id)
                previous = row[0]
                if previous == status:
                    return False
                if previous in ("completed","cancelled"):
                    raise ValueError("closed events cannot be silently reopened")
                conn.execute(
                    "UPDATE town_events SET status=%s,updated_at=now() WHERE event_id=%s",
                    (status,event_id))
                conn.execute(
                    "INSERT INTO town_event_history(event_id,action,details) VALUES (%s,%s,%s::jsonb)",
                    (event_id,"status_changed",json.dumps({"from":previous,"to":status,"note":note})))
                return True

    def recent(self, limit=12):
        if not 1 <= limit <= 50:
            raise ValueError("invalid limit")
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute(
                """SELECT event_id,title,location,event_time,status,details
                FROM town_events ORDER BY COALESCE(event_time,created_at) DESC,
                event_id DESC LIMIT %s""", (limit,)).fetchall()
        return [dict(zip(("id","title","location","when","status","details"),r))
                for r in rows]
