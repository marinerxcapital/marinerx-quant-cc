"""Decision engine (hard vetoes then factors)."""
from __future__ import annotations
from typing import Any

# Imports retained for future integration and type checking (even if not used in minimal decide)
from mcc.core.exceptions import RiskVeto  # noqa: F401
from mcc.strategy.lifecycle import StrategyStatus  # noqa: F401


def decide(
    has_green_strategy: bool,
    risk_veto: bool,
    data_ok: bool = True,
    session_ok: bool = True,
) -> dict[str, Any]:
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
