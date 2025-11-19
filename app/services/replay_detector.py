from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import md5
from typing import Deque, Dict, Tuple

from app.core.config import settings
from app.models import Transaction


@dataclass
class ReplayEntry:
    fingerprint: str
    timestamp: datetime


class ReplayDetector:
    """Simple in-memory replay attack detector.

    The detector fingerprints incoming transactions and keeps track of recent
    fingerprints within a sliding window. Transactions with duplicate
    fingerprints within the window are flagged as replay attempts.
    """

    def __init__(self, window_seconds: int | None = None) -> None:
        self.window_seconds = window_seconds or settings.replay_window_seconds
        self._entries: Deque[ReplayEntry] = deque()
        self._seen: Dict[str, datetime] = {}

    def _fingerprint(self, transaction: Transaction) -> str:
        parts = [
            getattr(transaction, field)
            for field in settings.duplicate_fingerprint_fields
        ]
        payload = "|".join(map(str, parts))
        if transaction.device_id:
            payload += f"|{transaction.device_id}"
        return md5(payload.encode("utf-8")).hexdigest()

    def _evict_expired(self, now: datetime) -> None:
        expiry = now - timedelta(seconds=self.window_seconds)
        while self._entries and self._entries[0].timestamp < expiry:
            old = self._entries.popleft()
            self._seen.pop(old.fingerprint, None)

    def is_replay(self, transaction: Transaction) -> Tuple[bool, str | None]:
        now = transaction.timestamp
        self._evict_expired(now)
        fingerprint = self._fingerprint(transaction)
        if fingerprint in self._seen:
            original_ts = self._seen[fingerprint]
            message = (
                "Duplicate fingerprint detected. Possible replay or bot-driven transaction "
                f"(first seen at {original_ts.isoformat()})."
            )
            return True, message

        self._entries.append(ReplayEntry(fingerprint=fingerprint, timestamp=now))
        self._seen[fingerprint] = now
        return False, None
