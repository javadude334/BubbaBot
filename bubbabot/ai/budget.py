"""Persistent, conservative monthly cloud spend tracker (USD)."""
import json
import os
import threading
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


class MonthlyBudget:
    def __init__(self, path: str, limit: str = "1.00", warning: str = "0.75"):
        self.path = Path(path)
        self.limit = Decimal(limit)
        self.warning = Decimal(warning)
        self._lock = threading.RLock()

    def _month(self):
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def _load(self):
        if not self.path.exists():
            return {"month": self._month(), "spent": "0"}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data if data.get("month") == self._month() else {"month": self._month(), "spent": "0"}

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, self.path)

    def remaining(self):
        with self._lock:
            return max(Decimal("0"), self.limit - Decimal(self._load()["spent"]))

    def can_spend(self, estimate: Decimal):
        with self._lock:
            return estimate >= 0 and estimate <= self.remaining()

    def charge(self, amount: Decimal):
        if amount < 0:
            raise ValueError("negative charge")
        with self._lock:
            data = self._load()
            data["spent"] = str(Decimal(data["spent"]) + amount)
            self._save(data)
            return Decimal(data["spent"])

    def status(self):
        with self._lock:
            spent = Decimal(self._load()["spent"])
            return {"spent": spent, "remaining": max(Decimal("0"), self.limit - spent),
                    "warning": spent >= self.warning}
