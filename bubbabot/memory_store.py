"""Local, opt-in-friendly visitor memory store for BubbaBot.

Stores limited, explicitly selected notes. Do not save raw chat logs here.
No network access and no external Python dependencies.
"""
import sqlite3
import time
from pathlib import Path


class VisitorMemory:
    def __init__(self, database_path, *, max_notes=12, retention_days=90, clock=None):
        if max_notes < 1 or retention_days < 1:
            raise ValueError("memory limits must be positive")
        self.database_path = str(database_path)
        self.max_notes = max_notes
        self.retention_seconds = retention_days * 86400
        self.clock = clock or time.time
        if self.database_path != ":memory:":
            parent = Path(self.database_path).parent
            if not parent.exists():
                raise FileNotFoundError(f"memory directory does not exist: {parent}")
        self._db = sqlite3.connect(self.database_path)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                bbs TEXT NOT NULL,
                handle TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                PRIMARY KEY (bbs, handle, note)
            )
        """)
        self._db.commit()

    @staticmethod
    def _identity(bbs, handle):
        if not isinstance(bbs, str) or not isinstance(handle, str):
            raise ValueError("bbs and handle must be strings")
        bbs, handle = bbs.strip().casefold(), handle.strip().casefold()
        if not bbs or not handle or len(bbs) > 100 or len(handle) > 100:
            raise ValueError("invalid visitor identity")
        return bbs, handle

    def remember(self, bbs, handle, note):
        """Save a short note explicitly approved for storage by the caller."""
        bbs, handle = self._identity(bbs, handle)
        if not isinstance(note, str) or not note.strip() or len(note) > 240:
            raise ValueError("note must contain 1-240 characters")
        now = self.clock()
        self.prune()
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO notes VALUES (?, ?, ?, ?, ?)",
                (bbs, handle, note.strip(), now, now + self.retention_seconds),
            )
            self._db.execute("""
                DELETE FROM notes WHERE bbs=? AND handle=? AND note NOT IN (
                    SELECT note FROM notes WHERE bbs=? AND handle=?
                    ORDER BY created_at DESC, rowid DESC LIMIT ?
                )
            """, (bbs, handle, bbs, handle, self.max_notes))

    def recall(self, bbs, handle):
        bbs, handle = self._identity(bbs, handle)
        now = self.clock()
        return [
            row[0] for row in self._db.execute(
                """SELECT note FROM notes WHERE bbs=? AND handle=?
                   AND expires_at>? ORDER BY created_at DESC LIMIT ?""",
                (bbs, handle, now, self.max_notes),
            )
        ]

    def forget(self, bbs, handle):
        bbs, handle = self._identity(bbs, handle)
        with self._db:
            cursor = self._db.execute(
                "DELETE FROM notes WHERE bbs=? AND handle=?", (bbs, handle)
            )
        return cursor.rowcount

    def prune(self):
        with self._db:
            self._db.execute("DELETE FROM notes WHERE expires_at<=?", (self.clock(),))

    def close(self):
        self._db.close()
