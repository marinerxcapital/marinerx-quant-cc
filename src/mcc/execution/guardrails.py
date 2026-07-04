"""Execution guardrails (P1 + P2 hard)."""
from __future__ import annotations
from mcc.core.exceptions import ExecutionBlocked, RiskVeto
from mcc.strategy.lifecycle import StrategyStatus

def check_pre_trade(strategy_status: StrategyStatus, risk_veto: bool, size_ok: bool) -> None:
    if strategy_status != StrategyStatus.GREEN:
        raise ExecutionBlocked("strategy status != GREEN (validation-first)")
    if risk_veto:
        raise RiskVeto("risk veto active (PropGuardian LOCKOUT or limit breach)")
    if not size_ok:
        raise ExecutionBlocked("size exceeds risk recommendation or caps")
