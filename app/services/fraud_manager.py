from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.models import Transaction, TransactionAssessment
from app.services.replay_detector import ReplayDetector
from app.services.risk_profiler import RiskProfiler
from app.services.velocity_checker import VelocityChecker


@dataclass
class FraudManager:
    replay_detector: ReplayDetector
    velocity_checker: VelocityChecker
    risk_profiler: RiskProfiler

    def assess(self, transaction: Transaction) -> TransactionAssessment:
        reasons: List[str] = []
        blocked = False

        is_replay, replay_reason = self.replay_detector.is_replay(transaction)
        if is_replay:
            reasons.append(replay_reason or "Replay attack detected")
            blocked = True

        velocity_reasons = self.velocity_checker.register(transaction)
        if velocity_reasons:
            reasons.extend(velocity_reasons)
            blocked = True

        recent_velocity = transaction.previous_velocity or len(
            self.velocity_checker._events.get(transaction.consumer_id, [])  # type: ignore[attr-defined]
        )
        risk_result = self.risk_profiler.score(transaction, recent_velocity)
        if risk_result.reasons and not blocked:
            # Promote decision to review if not already blocked
            blocked = risk_result.score >= 0.9
            reasons.extend(risk_result.reasons)

        decision = "block" if blocked else "approve"
        if risk_result.reasons and not blocked:
            decision = "review"

        if not reasons:
            reasons.append("Transaction passed all policy, velocity, and risk checks")

        return TransactionAssessment(
            transaction_id=transaction.transaction_id,
            decision=decision,
            risk_score=risk_result.score,
            reasons=reasons,
            blocked=blocked,
        )


def create_manager() -> FraudManager:
    return FraudManager(
        replay_detector=ReplayDetector(),
        velocity_checker=VelocityChecker(),
        risk_profiler=RiskProfiler(),
    )
