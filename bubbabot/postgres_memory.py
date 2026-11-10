"""PostgreSQL storage for approved, non-PII visitor memory notes.

This is a storage adapter, not a PII detector. Only pass notes that have
already been screened. Do not connect this to automatic chat extraction yet.
"""
import hashlib
import hmac
import time

import psycopg


class PostgresVisitorMemory:
    def __init__(self, *, secret, dsn="dbname=bubbabot user=bubbabot", max_notes=12, retention_days=90):
        if not isinstance(secret, (bytes, bytearray)) or len(secret) < 32:
            raise ValueError("a private 32+ byte HMAC key is required")
        if max_notes < 1 or retention_days < 1:
            raise ValueError("limits must be positive")
        self.secret = bytes(secret)
        self.dsn = dsn
        self.max_notes = max_notes
        self.retention_seconds = retention_days * 86400

    def _key(self, bbs, handle):
        if not isinstance(bbs, str) or not isinstance(handle, str):
            raise ValueError("invalid identity")
        bbs, handle = bbs.strip().casefold(), handle.strip().casefold()
        if not bbs or not handle or len(bbs) > 100 or len(handle) > 100:
            raise ValueError("invalid identity")
        payload = (bbs + "\x00" + handle).encode("utf-8")
        return hmac.new(self.secret, payload, hashlib.sha256).hexdigest()

    def initialize(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visitor_memory (
                    visitor_key char(64) NOT NULL,
                    note text NOT NULL CHECK (char_length(note) BETWEEN 1 AND 240),
                    created_at timestamptz NOT NULL DEFAULT now(),
                    expires_at timestamptz NOT NULL,
                    PRIMARY KEY (visitor_key, note)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS visitor_memory_expiry_idx
                ON visitor_memory (expires_at)
            """)

    def remember_screened(self, bbs, handle, note):
        """Caller must have explicitly screened note for PII/sensitivity."""
        if not isinstance(note, str) or not note.strip() or len(note.strip()) > 240:
            raise ValueError("note must contain 1-240 characters")
        key = self._key(bbs, handle)
        with psycopg.connect(self.dsn) as conn:
            with conn.transaction():
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))
                conn.execute("DELETE FROM visitor_memory WHERE expires_at <= now()")
                conn.execute("""
                    INSERT INTO visitor_memory (visitor_key, note, expires_at)
                    VALUES (%s, %s, now() + (%s * interval '1 second'))
                    ON CONFLICT (visitor_key, note)
                    DO UPDATE SET created_at = now(), expires_at = EXCLUDED.expires_at
                """, (key, note.strip(), self.retention_seconds))
                conn.execute("""
                    DELETE FROM visitor_memory
                    WHERE visitor_key = %s AND note NOT IN (
                        SELECT note FROM visitor_memory WHERE visitor_key = %s
                        ORDER BY created_at DESC, note DESC LIMIT %s
                    )
                """, (key, key, self.max_notes))

    def recall(self, bbs, handle):
        key = self._key(bbs, handle)
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("""
                SELECT note FROM visitor_memory
                WHERE visitor_key = %s AND expires_at > now()
                ORDER BY created_at DESC, note DESC LIMIT %s
            """, (key, self.max_notes)).fetchall()
        return [r[0] for r in rows]

    def forget(self, bbs, handle):
        key = self._key(bbs, handle)
        with psycopg.connect(self.dsn) as conn:
            return conn.execute(
                "DELETE FROM visitor_memory WHERE visitor_key = %s", (key,)
            ).rowcount

    def prune(self):
        with psycopg.connect(self.dsn) as conn:
            return conn.execute(
                "DELETE FROM visitor_memory WHERE expires_at <= now()"
            ).rowcount
