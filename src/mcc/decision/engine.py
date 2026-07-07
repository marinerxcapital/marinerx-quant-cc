"""Trade-or-no-trade decision engine with factor scoring and hard vetoes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mcc.risk.command import get_risk_state
from mcc.storage.repositories import DecisionRepository, StrategyRepository
from mcc.system.state import build_data_freshness

FACTOR_WEIGHTS = {
    "strategy_validation": 0.25,
    "regime_alignment": 0.20,
    "risk_headroom": 0.20,
    "event_filter": 0.10,
    "data_freshness": 0.10,
    "market_confirmation": 0.10,
    "manual_override": 0.05,
}

_repo = DecisionRepository()
_strategy_repo = StrategyRepository()


def evaluate_decision(payload: dict[str, Any]) -> dict[str, Any]:
    symbol = (payload.get("symbol") or "NQ").strip().upper()
    strategy_id = payload.get("strategy_id")
    event_lockout = bool(payload.get("event_lockout", False))
    manual_notes = payload.get("manual_notes", "")

    risk = get_risk_state()
    freshness = build_data_freshness()
    strategy = _strategy_repo.get(strategy_id) if strategy_id else None

    vetoes: list[str] = []
    stand_aside: list[str] = []
    factor_scores: dict[str, float] = {k: 0.0 for k in FACTOR_WEIGHTS}

    # Hard vetoes — NO-GO
    if risk.get("kill_switch_active"):
        vetoes.append("kill_switch_active")
    market_status = freshness["sources"]["market_data"]["status"]
    if market_status in ("stale", "missing"):
        vetoes.append("data_stale")
    if risk.get("current_day_pnl", 0) <= -risk.get("daily_loss_limit", 0):
        vetoes.append("daily_loss_limit_hit")
    if strategy and strategy.get("status") == "RED":
        vetoes.append("strategy_red")
    daily_remaining = risk.get("daily_loss_remaining", 0)
    if daily_remaining < 100:
        vetoes.append("risk_headroom_insufficient")

    # STAND-ASIDE vetoes
    if not strategy:
        stand_aside.append("no_validated_strategy")
    elif strategy.get("status") not in ("GREEN", "YELLOW", "TESTED"):
        stand_aside.append("no_validated_strategy")
    if event_lockout:
        stand_aside.append("event_lockout")

    # Factor scores
    if strategy:
        status = strategy.get("status", "DRAFT")
        factor_scores["strategy_validation"] = {
            "GREEN": 90, "YELLOW": 60, "TESTED": 70, "REGISTERED": 40,
        }.get(status, 20)
    factor_scores["regime_alignment"] = 50.0
    factor_scores["risk_headroom"] = min(100.0, max(0.0, daily_remaining / max(risk.get("daily_loss_limit", 1), 1) * 100))
    factor_scores["event_filter"] = 0.0 if event_lockout else 80.0
    factor_scores["data_freshness"] = 90.0 if market_status == "fresh" else 20.0
    factor_scores["market_confirmation"] = 60.0
    factor_scores["manual_override"] = 50.0 if manual_notes else 0.0

    weighted = sum(factor_scores[k] * FACTOR_WEIGHTS[k] for k in FACTOR_WEIGHTS)
    confidence = weighted / 100.0
    if market_status != "fresh":
        confidence = min(confidence, 0.5)

    regime_snapshot = payload.get("regime_snapshot") or {"status": "unavailable", "degraded": True}
    if regime_snapshot.get("status") == "unavailable":
        confidence *= 0.85

    decision: str
    rationale: str
    if vetoes:
        decision = "NO-GO"
        rationale = "Hard veto(s): " + ", ".join(vetoes)
    elif stand_aside:
        decision = "STAND-ASIDE"
        rationale = "Stand-aside condition(s): " + ", ".join(stand_aside)
    elif weighted >= 75:
        decision = "GO"
        rationale = "Factor score meets GO threshold."
    elif weighted >= 50:
        decision = "STAND-ASIDE"
        rationale = "Factor score in marginal range."
    else:
        decision = "NO-GO"
        rationale = "Factor score below minimum threshold."

    result = {
        "symbol": symbol,
        "strategy_id": strategy_id,
        "decision": decision,
        "confidence": round(confidence, 4),
        "rationale": rationale,
        "vetoes": vetoes + stand_aside,
        "factor_scores": {k: round(v, 2) for k, v in factor_scores.items()},
        "risk_snapshot": risk,
        "data_freshness_snapshot": freshness,
        "strategy_verdict": strategy.get("latest_verdict", "") if strategy else "",
        "regime_snapshot": regime_snapshot,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    saved = _repo.save(result)
    result["decision_id"] = saved["decision_id"]
    return result


def decide(
    has_green_strategy: bool,
    risk_veto: bool,
    data_ok: bool = True,
    session_ok: bool = True,
) -> dict[str, Any]:
    """Legacy minimal decide for backward compatibility."""
    vetoes: list[str] = []
    if not has_green_strategy:
        vetoes.append("validation")
    if risk_veto:
        vetoes.append("risk")
    if not data_ok:
        vetoes.append("data-health")
    if not session_ok:
        vetoes.append("session")
    if vetoes:
        return {"decision": "NO_GO", "vetoes": vetoes, "reason": "hard veto: " + ",".join(vetoes)}
    return {"decision": "GO", "reason": "vetoes clear, factors acceptable"}