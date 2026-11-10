"""Persistent memory opt-out preferences.

Preferences contain only HMAC-derived visitor keys. No chat content or raw
MRC handles are stored. This module does not enable memory collection.
"""
import psycopg


class MemoryPreferences:
    def __init__(self, memory_store):
        self.memory = memory_store

    def initialize(self):
        with psycopg.connect(self.memory.dsn) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visitor_memory_preferences (
                    visitor_key char(64) PRIMARY KEY,
                    opted_out boolean NOT NULL DEFAULT false,
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
            """)

    def is_enabled(self, bbs, handle):
        key = self.memory._key(bbs, handle)
        with psycopg.connect(self.memory.dsn) as conn:
            row = conn.execute(
                "SELECT opted_out FROM visitor_memory_preferences WHERE visitor_key=%s",
                (key,),
            ).fetchone()
        return row is None or not row[0]

    def disable_and_forget(self, bbs, handle):
        """Opt out and delete existing notes in a single DB transaction."""
        key = self.memory._key(bbs, handle)
        with psycopg.connect(self.memory.dsn) as conn:
            with conn.transaction():
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))
                conn.execute("""
                    INSERT INTO visitor_memory_preferences(visitor_key, opted_out)
                    VALUES (%s, true)
                    ON CONFLICT(visitor_key) DO UPDATE
                    SET opted_out=true, updated_at=now()
                """, (key,))
                conn.execute("DELETE FROM visitor_memory WHERE visitor_key=%s", (key,))

    def enable(self, bbs, handle):
        key = self.memory._key(bbs, handle)
        with psycopg.connect(self.memory.dsn) as conn:
            conn.execute("""
                INSERT INTO visitor_memory_preferences(visitor_key, opted_out)
                VALUES (%s, false)
                ON CONFLICT(visitor_key) DO UPDATE
                SET opted_out=false, updated_at=now()
            """, (key,))

    def forget(self, bbs, handle):
        return self.memory.forget(bbs, handle)
