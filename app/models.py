from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class RiskProfile(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier provided by the upstream system")
    consumer_id: str
    merchant_id: str
    channel: str = Field(..., description="Transaction channel such as web, mobile, IVR")
    amount: float
    currency: str = "USD"
    location: Optional[str] = Field(
        None, description="Country or region where the transaction originated"
    )
    device_id: Optional[str] = None
    previous_velocity: Optional[int] = Field(
        None, description="Optional historical velocity information from upstream systems"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    risk_profile: RiskProfile = RiskProfile.medium

    @validator("amount")
    def positive_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be positive")
        return value


class TransactionAssessment(BaseModel):
    transaction_id: str
    decision: str
    risk_score: float
    reasons: list[str]
    blocked: bool = False


class HealthResponse(BaseModel):
    status: str
    velocity_window_seconds: int
    replay_window_seconds: int
