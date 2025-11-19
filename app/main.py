from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.models import HealthResponse, Transaction, TransactionAssessment
from app.services.fraud_manager import create_manager

app = FastAPI(title="Fraud Management System", version="0.1.0")
manager = create_manager()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        velocity_window_seconds=settings.window_seconds,
        replay_window_seconds=settings.replay_window_seconds,
    )


@app.post("/transactions", response_model=TransactionAssessment)
def evaluate_transaction(transaction: Transaction) -> TransactionAssessment:
    assessment = manager.assess(transaction)
    if assessment.blocked:
        raise HTTPException(status_code=403, detail=assessment.dict())
    return assessment
