from __future__ import annotations

from pydantic import BaseModel, Field


class VelocityThresholds(BaseModel):
    max_transactions: int = Field(
        ..., description="Maximum number of transactions allowed within the window"
    )
    max_total_amount: float = Field(
        ..., description="Maximum total amount allowed within the window"
    )


class Settings(BaseModel):
    window_seconds: int = 60
    replay_window_seconds: int = 120
    duplicate_fingerprint_fields: tuple[str, ...] = ("consumer_id", "merchant_id", "amount")
    base_velocity_thresholds: dict[str, VelocityThresholds] = Field(
        default_factory=lambda: {
            "low": VelocityThresholds(max_transactions=12, max_total_amount=20000.0),
            "medium": VelocityThresholds(max_transactions=8, max_total_amount=10000.0),
            "high": VelocityThresholds(max_transactions=4, max_total_amount=4000.0),
        }
    )
    base_risk_threshold: float = 0.65
    review_threshold: float = 0.5


settings = Settings()
