from __future__ import annotations

from datetime import datetime, timezone
import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .eval_engine import evaluate_select_150k_eval
from .models import AccountPhase, AccountSnapshot, DayResult, SignalIntent
from .payout_engine import calculate_flex_payout
from .risk_engine import gate_trade

router = APIRouter(prefix="/api/tradeify/150k", tags=["Tradeify 150K"])


class EvalRequest(BaseModel):
    total_profit: float
    largest_winning_day: float


class DayResultPayload(BaseModel):
    date: str
    realized_pnl: float


class PayoutRequest(BaseModel):
    balance: float
    day_results: list[DayResultPayload]


class AccountSnapshotPayload(BaseModel):
    phase: AccountPhase
    balance: float
    eod_drawdown_floor: float
    realized_day_pnl: float
    open_trade_risk: float = 0.0
    largest_winning_day: float = 0.0
    total_eval_profit: float = 0.0


class SignalPayload(BaseModel):
    symbol: str = Field(..., examples=["MNQ", "MES", "MCL", "MGC"])
    direction: str
    setup_name: str
    entry_price: float
    stop_price: float
    target_price: float
    contract_type: str = "micro"
    requested_contracts: int = 1


class GateRequest(BaseModel):
    snapshot: AccountSnapshotPayload
    signal: SignalPayload


@router.get("/rules")
def rules_summary():
    return {
        "account": "Tradeify Select Flex 150K",
        "evaluation": {
            "profit_target": 9000,
            "max_drawdown_eod": 4500,
            "daily_loss_limit": None,
            "consistency_max_single_day_pct": 0.40,
            "max_contracts": "12 mini / 120 micro",
        },
        "funded_flex": {
            "winning_days_required": 5,
            "winning_day_threshold": 250,
            "max_payout_gross": 5000,
            "payout_formula": "50% of total profits, capped at $5,000",
            "profit_split": "90/10 trader/firm",
        },
        "marinerx_policy": {
            "max_risk_per_trade": 250,
            "max_daily_loss": 750,
            "hard_daily_stop": 900,
            "emergency_flatten_headroom": 1500,
            "mode_default": "paper-first; execution inert until explicitly enabled",
        },
    }


@router.post("/eval/status")
def eval_status(req: EvalRequest):
    return evaluate_select_150k_eval(req.total_profit, req.largest_winning_day).__dict__


@router.post("/payout/status")
def payout_status(req: PayoutRequest):
    days = [DayResult(date=d.date, realized_pnl=d.realized_pnl) for d in req.day_results]
    return calculate_flex_payout(balance=req.balance, day_results=days).__dict__


@router.post("/risk/gate")
def risk_gate(req: GateRequest):
    snapshot = AccountSnapshot(
        phase=req.snapshot.phase,
        balance=req.snapshot.balance,
        eod_drawdown_floor=req.snapshot.eod_drawdown_floor,
        realized_day_pnl=req.snapshot.realized_day_pnl,
        open_trade_risk=req.snapshot.open_trade_risk,
        largest_winning_day=req.snapshot.largest_winning_day,
        total_eval_profit=req.snapshot.total_eval_profit,
    )
    signal = SignalIntent(**req.signal.model_dump())
    return gate_trade(snapshot, signal).__dict__


@router.get("/data/status")
def data_status():
    enabled = os.getenv("MARINERX_TRADEIFY_DATA_ENABLED", "true").lower() == "true"
    tradovate_enabled = os.getenv("MARINERX_TRADOVATE_ENABLED", "true").lower() == "true"
    dashboard_enabled = os.getenv("MARINERX_TRADEIFY_DASHBOARD_ENABLED", "false").lower() == "true"
    live_orders = os.getenv("MARINERX_ALLOW_LIVE_ORDERS", "false").lower() == "true"
    return {
        "enabled": enabled,
        "tradovate_enabled": tradovate_enabled,
        "tradeify_dashboard_enabled": dashboard_enabled,
        "live_orders_enabled": live_orders,
        "mode": os.getenv("MARINERX_TRADEIFY_MODE", "PAPER_FIRST"),
        "status": "configured" if enabled else "disabled",
        "message": "Connector implementation scaffolded. Complete Tradovate API + Tradeify dashboard adapters before enabling live sync.",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/data/sync")
def data_sync_placeholder():
    return {
        "status": "not_implemented",
        "safe_default": "BLOCK_NEW_TRADES",
        "message": "Data sync is intentionally inert in this package. Implement TradovateConnector and TradeifyDashboardConnector in the target repo.",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/data/latest")
def data_latest_placeholder():
    return {
        "status": "not_available",
        "safe_default": "BLOCK_NEW_TRADES",
        "message": "No cached account snapshot is bundled with this package. The target repo must persist live normalized snapshots.",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/data/health")
def data_health():
    return {
        "status": "scaffold_ready",
        "tradovate_connector": "pending_implementation",
        "tradeify_dashboard_connector": "pending_implementation",
        "safe_default": "BLOCK_NEW_TRADES",
        "live_orders_enabled": os.getenv("MARINERX_ALLOW_LIVE_ORDERS", "false").lower() == "true",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/data/validate-session")
def validate_session_placeholder():
    return {
        "status": "not_implemented",
        "dashboard_session_valid": False,
        "safe_default": "BLOCK_NEW_TRADES",
        "message": "Implement Playwright storage_state validation in target repo.",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/data/reconcile")
def reconcile_placeholder():
    return {
        "status": "not_implemented",
        "reconciliation": "unavailable",
        "safe_default": "BLOCK_NEW_TRADES",
        "message": "Implement Tradovate-vs-Tradeify reconciliation after live data adapters are completed.",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
