"""Backtest API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mcc.research.backtesting import run_backtest

router = APIRouter(prefix="/api/backtests", tags=["backtests"])


class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str = ""
    timeframe: str = "15m"
    start_date: str = ""
    end_date: str = ""
    initial_equity: float = 100000.0
    risk_per_trade: float = 350.0
    commission_per_contract: float = 2.5
    slippage_ticks: float = 1.0
    use_demo_data: bool = False


@router.post("/run")
def run_backtest_endpoint(body: BacktestRequest) -> dict[str, Any]:
    result = run_backtest(body.model_dump())
    if "error" in result:
        if result["error"] == "strategy_not_found":
            raise HTTPException(404, result["message"])
        raise HTTPException(400, result["message"])
    return result