from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, List

from app.core.config import VelocityThresholds, settings
from app.models import RiskProfile, Transaction


@dataclass
class VelocityEvent:
    timestamp: datetime
    amount: float
    merchant_id: str


class VelocityChecker:
    """Tracks transaction velocity per consumer and risk profile."""

    def __init__(self, window_seconds: int | None = None) -> None:
        self.window_seconds = window_seconds or settings.window_seconds
        self._events: Dict[str, Deque[VelocityEvent]] = defaultdict(deque)

    def _thresholds(self, profile: RiskProfile) -> VelocityThresholds:
        return settings.base_velocity_thresholds[profile.value]

    def _evict_expired(self, consumer_id: str, now: datetime) -> None:
        expiry = now - timedelta(seconds=self.window_seconds)
        events = self._events[consumer_id]
        while events and events[0].timestamp < expiry:
            events.popleft()
        if not events:
            self._events.pop(consumer_id, None)

    def register(self, transaction: Transaction) -> List[str]:
        now = transaction.timestamp
        consumer_events = self._events[transaction.consumer_id]
        consumer_events.append(
            VelocityEvent(timestamp=now, amount=transaction.amount, merchant_id=transaction.merchant_id)
        )
        self._evict_expired(transaction.consumer_id, now)

        reasons: List[str] = []
        thresholds = self._thresholds(transaction.risk_profile)
        if len(consumer_events) > thresholds.max_transactions:
            reasons.append(
                "Velocity threshold exceeded: transaction count within window exceeds permitted limit"
            )

        total_amount = sum(event.amount for event in consumer_events)
        if total_amount > thresholds.max_total_amount:
            reasons.append(
                "Risk-based cumulative amount limit exceeded within the rolling window"
            )

        if len(consumer_events) >= 2:
            prev = consumer_events[-2]
            if prev.merchant_id == transaction.merchant_id and prev.amount == transaction.amount:
                reasons.append(
                    "Detected consecutive transactions with identical merchant and amount. Possible automation or replay."
                )

        return reasons
