"""Trade-or-no-trade decision API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcc.decision.engine import evaluate_decision

router = APIRouter(prefix="/api/decision", tags=["decision"])


class DecisionEvaluateRequest(BaseModel):
    symbol: str = "NQ"
    strategy_id: str | None = None
    account_id: str | None = None
    session_context: dict[str, Any] = Field(default_factory=dict)
    manual_notes: str = ""
    event_lockout: bool = False
    regime_snapshot: dict[str, Any] | None = None


@router.post("/evaluate")
def evaluate(body: DecisionEvaluateRequest) -> dict[str, Any]:
    return evaluate_decision(body.model_dump())