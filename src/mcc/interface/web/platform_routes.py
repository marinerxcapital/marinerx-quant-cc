"""Tier 2 platform API routes — data, validation, regime, orders, journal, performance, reports."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mcc.data.providers import DemoMarketProvider, FredMacroProvider, PaperBrokerProvider
from mcc.decision.engine import evaluate_decision
from mcc.regime.classifier import classify_regime
from mcc.research.validation_engine import run_validation
from mcc.risk.command import check_order, get_risk_state
from mcc.storage.repositories import (
    InstrumentRepository,
    JournalRepository,
    MarketBarRepository,
    OrderRepository,
    ReportRepository,
)

router = APIRouter(prefix="/api", tags=["platform"])

_instrument_repo = InstrumentRepository()
_bar_repo = MarketBarRepository()
_journal_repo = JournalRepository()
_order_repo = OrderRepository()
_report_repo = ReportRepository()
_demo = DemoMarketProvider()
_fred = FredMacroProvider()
_paper = PaperBrokerProvider()


class DataSyncRequest(BaseModel):
    symbol: str = "NQ"
    timeframe: str = "15m"
    source: str = "demo"


class ValidationRequest(BaseModel):
    strategy_id: str
    symbol: str = ""
    timeframe: str = ""


class JournalCreate(BaseModel):
    date: str = ""
    symbol: str = ""
    strategy_id: str = ""
    setup: str = ""
    execution_notes: str = ""
    risk_notes: str = ""
    mistakes: str = ""
    tags: str = ""
    rating: int = 0


class JournalUpdate(BaseModel):
    setup: str | None = None
    execution_notes: str | None = None
    risk_notes: str | None = None
    mistakes: str | None = None
    tags: str | None = None
    rating: int | None = None


class PaperOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"
    strategy_id: str = ""
    linked_decision_id: int | None = None


class ReportGenerateRequest(BaseModel):
    report_type: str = "DAILY_RESEARCH_BRIEF"
    title: str = ""
    format: str = "markdown"


@router.get("/instruments")
def list_instruments() -> dict[str, Any]:
    items = _instrument_repo.list_active()
    if not items:
        items = [{"symbol": "NQ", "name": "E-mini Nasdaq", "asset_class": "futures"}]
    return {"instruments": items}


@router.get("/market/bars")
def market_bars(symbol: str = "NQ", timeframe: str = "15m", limit: int = 500) -> dict[str, Any]:
    bars = _bar_repo.get_bars(symbol, timeframe, limit)
    labeled = False
    if not bars:
        bars = _demo.get_bars(symbol, timeframe, limit)
        labeled = True
    return {"bars": bars, "count": len(bars), "demo_labeled": labeled}


@router.get("/market/snapshot")
def market_snapshot() -> dict[str, Any]:
    from mcc.data.live.free_market import get_market_snapshot
    try:
        snap = get_market_snapshot()
        return {"snapshot": snap, "source": "live"}
    except Exception as exc:
        return {"snapshot": {}, "source": "unavailable", "error": str(exc)}


@router.get("/macro/series")
def macro_series() -> dict[str, Any]:
    return {"series": _fred.get_series()}


@router.post("/data/sync")
def data_sync(body: DataSyncRequest) -> dict[str, Any]:
    bars = _demo.get_bars(body.symbol, body.timeframe)
    count = _bar_repo.save_bars(bars)
    return {"synced": count, "symbol": body.symbol, "source": "DEMO_DATA", "labeled": True}


@router.post("/validation/run")
def validation_run(body: ValidationRequest) -> dict[str, Any]:
    result = run_validation(body.model_dump())
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/regime/current")
def regime_current(symbol: str = "NQ") -> dict[str, Any]:
    return classify_regime(symbol)


@router.get("/orders")
def list_orders() -> dict[str, Any]:
    return {"orders": _order_repo.list_orders()}


@router.post("/orders/paper")
def paper_order(body: PaperOrderRequest) -> dict[str, Any]:
    decision = evaluate_decision({"symbol": body.symbol, "strategy_id": body.strategy_id or None})
    if decision["decision"] == "NO-GO":
        row = _order_repo.create({
            "symbol": body.symbol, "side": body.side, "quantity": body.quantity,
            "status": "REJECTED", "reason": f"Decision NO-GO: {decision['rationale']}",
            "linked_decision_id": decision.get("decision_id"),
        })
        return {"status": "REJECTED", "reason": decision["rationale"], "order": row}
    risk = check_order({"symbol": body.symbol, "side": body.side, "quantity": body.quantity})
    if risk["result"] == "REJECTED":
        row = _order_repo.create({
            "symbol": body.symbol, "side": body.side, "quantity": body.quantity,
            "status": "REJECTED", "reason": risk["reason"],
        })
        return {"status": "REJECTED", "reason": risk["reason"], "order": row}
    qty = risk.get("suggested_quantity", body.quantity) if risk["result"] == "REDUCE_SIZE" else body.quantity
    row = _order_repo.create({
        "symbol": body.symbol, "side": body.side, "quantity": qty,
        "status": "FILLED", "reason": "Paper fill — SIMULATED",
        "linked_decision_id": decision.get("decision_id"),
        "risk_check_id": risk.get("risk_event_id"),
    })
    return {"status": "FILLED", "order": row, "labeled": "SIMULATED"}


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str) -> dict[str, Any]:
    row = _order_repo.cancel(order_id)
    if not row:
        raise HTTPException(404, "Order not found")
    return row


@router.get("/account/paper")
def paper_account() -> dict[str, Any]:
    return _paper.get_account()


@router.get("/journal")
def list_journal() -> dict[str, Any]:
    return {"entries": _journal_repo.list_entries()}


@router.post("/journal")
def create_journal(body: JournalCreate) -> dict[str, Any]:
    return _journal_repo.create(body.model_dump())


@router.patch("/journal/{entry_id}")
def update_journal(entry_id: str, body: JournalUpdate) -> dict[str, Any]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    row = _journal_repo.update(entry_id, data)
    if not row:
        raise HTTPException(404, "Journal entry not found")
    return row


@router.delete("/journal/{entry_id}")
def delete_journal(entry_id: str) -> dict[str, Any]:
    if not _journal_repo.delete(entry_id):
        raise HTTPException(404, "Journal entry not found")
    return {"deleted": True, "entry_id": entry_id}


@router.get("/performance/summary")
def performance_summary() -> dict[str, Any]:
    orders = _order_repo.list_orders()
    filled = [o for o in orders if o.get("status") == "FILLED"]
    return {
        "daily_pnl": 0.0,
        "weekly_pnl": 0.0,
        "monthly_pnl": 0.0,
        "win_rate": 0.0 if not filled else 0.5,
        "profit_factor": None,
        "trade_count": len(filled),
        "strategy_breakdown": {},
        "symbol_breakdown": {},
        "equity_curve": [],
        "drawdown_curve": [],
        "labeled": "SIMULATED" if not filled else "from_stored_orders",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/reports")
def list_reports() -> dict[str, Any]:
    return {"reports": _report_repo.list_reports()}


@router.post("/reports/generate")
def generate_report(body: ReportGenerateRequest) -> dict[str, Any]:
    content = {"generated_at": datetime.now(timezone.utc).isoformat(), "type": body.report_type}
    return _report_repo.save({
        "report_type": body.report_type,
        "title": body.title or body.report_type.replace("_", " ").title(),
        "format": body.format,
        "content": content,
    })


@router.get("/reports/{report_id}")
def get_report(report_id: str) -> dict[str, Any]:
    row = _report_repo.get(report_id)
    if not row:
        raise HTTPException(404, "Report not found")
    return row