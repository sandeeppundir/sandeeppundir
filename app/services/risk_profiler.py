from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import settings
from app.models import RiskProfile, Transaction


@dataclass
class RiskResult:
    score: float
    reasons: List[str]


class RiskProfiler:
    """AI-powered risk profiler built on an Isolation Forest model."""

    def __init__(self) -> None:
        self._model = self._train_model()

    def _train_model(self) -> IsolationForest:
        # Synthetic dataset that represents benign behavior
        rng = np.random.default_rng(42)
        amounts = rng.normal(loc=200, scale=80, size=500)
        velocities = rng.poisson(lam=3, size=500)
        distances = rng.normal(loc=50, scale=20, size=500)
        X = np.column_stack([amounts, velocities, distances])
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)
        return model

    def _feature_vector(self, transaction: Transaction, recent_velocity: int) -> np.ndarray:
        amount = transaction.amount
        velocity = recent_velocity
        distance_proxy = 0.0 if not transaction.location else len(transaction.location)
        return np.array([[amount, velocity, distance_proxy]], dtype=float)

    def _dynamic_threshold(self, profile: RiskProfile) -> Tuple[float, float]:
        base = settings.base_risk_threshold
        review = settings.review_threshold
        if profile == RiskProfile.high:
            return base - 0.15, review - 0.1
        if profile == RiskProfile.low:
            return base + 0.15, review + 0.1
        return base, review

    def score(self, transaction: Transaction, recent_velocity: int) -> RiskResult:
        features = self._feature_vector(transaction, recent_velocity)
        model_score = self._model.decision_function(features)[0]
        normalized = (1 - model_score) / 2  # convert to 0..1 risk probability
        threshold, review_threshold = self._dynamic_threshold(transaction.risk_profile)

        reasons: List[str] = []
        if normalized >= threshold:
            reasons.append(
                "IsolationForest flagged the transaction as anomalous compared to learned behavior"
            )
        elif normalized >= review_threshold:
            reasons.append("Risk exceeds review threshold; manual inspection recommended")

        # Heuristic: penalize large amounts relative to profile
        profile_multiplier = {RiskProfile.low: 1.5, RiskProfile.medium: 1.0, RiskProfile.high: 0.7}
        dynamic_limit = 2000 * profile_multiplier[transaction.risk_profile]
        if transaction.amount > dynamic_limit:
            reasons.append(
                f"Transaction amount {transaction.amount:.2f} exceeds dynamic limit {dynamic_limit:.2f}"
            )
            normalized = max(normalized, threshold)

        return RiskResult(score=float(normalized), reasons=reasons)
