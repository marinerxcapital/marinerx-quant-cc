"""Portfolio risk aggregation (Phase 08) + optimization constraint pass-through (Phase 16).

- Net/gross exposure
- Concentration flags
- Uses Phase-03 style correlation (simple stub, can take corr matrix)
- Flags correlated cluster risk.
- optimize_allocation delegates constraints to riskfolio_adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import pandas as pd

from mcc.risk.riskfolio_adapter import (
    DEFAULT_INSTRUMENTS,
    OptimizationMethod,
    PortfolioOptimizationResult,
    optimize_portfolio,
)

DEFAULT_POSITION_CAPS: dict[str, float] = {"NQ": 3.0, "ES": 3.0, "CL": 2.0, "GC": 2.0}


@dataclass(frozen=True)
class Exposure:
    gross: Decimal
    net: Decimal
    instruments: int
    concentration: float  # max |pos| / gross
    corr_risk_flag: bool
    reason: str


def build_constraints(
    position_caps: Mapping[str, float] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build constraint dict for riskfolio_adapter from per-instrument caps."""
    caps = dict(position_caps or DEFAULT_POSITION_CAPS)
    constraints: dict[str, Any] = {"max_position_cap": caps}
    if extra:
        constraints.update(dict(extra))
    return constraints


def aggregate_exposure(
    positions: Sequence[Dict[str, float | int | Decimal]],
    corr_matrix: Optional[Dict[Tuple[str, str], float]] = None,
    corr_threshold: float = 0.7,
) -> Exposure:
    """Aggregate positions.

    positions: list of {"symbol": "NQ", "qty": 2, "notional": 30020.0 or value}
    """
    if not positions:
        return Exposure(
            gross=Decimal(0), net=Decimal(0), instruments=0,
            concentration=0.0, corr_risk_flag=False, reason="no positions"
        )

    gross = Decimal(0)
    net = Decimal(0)
    sym_qty: Dict[str, Decimal] = {}
    max_abs = Decimal(0)

    for p in positions:
        sym = str(p.get("symbol", "UNK"))
        qty = Decimal(str(p.get("qty", p.get("position", 0))))
        notional = Decimal(str(p.get("notional", abs(float(qty)) * 15000)))
        gross += abs(notional)
        net += notional
        sym_qty[sym] = sym_qty.get(sym, Decimal(0)) + qty
        if abs(notional) > max_abs:
            max_abs = abs(notional)

    instruments = len(sym_qty)
    concentration = float(max_abs / gross) if gross > 0 else 0.0

    corr_risk_flag = False
    if corr_matrix and instruments > 1:
        for (s1, s2), c in corr_matrix.items():
            if abs(c) > corr_threshold and sym_qty.get(s1, 0) != 0 and sym_qty.get(s2, 0) != 0:
                if (sym_qty[s1] > 0) == (sym_qty[s2] > 0):
                    corr_risk_flag = True
                    break
    else:
        if instruments >= 2 and concentration > 0.6:
            corr_risk_flag = True

    reason = (
        f"agg: gross={float(gross):.2f} net={float(net):.2f} instr={instruments} "
        f"conc={concentration:.2f} corr_flag={corr_risk_flag}"
    )
    return Exposure(
        gross=gross, net=net, instruments=instruments,
        concentration=concentration, corr_risk_flag=corr_risk_flag, reason=reason
    )


def concentration_risk(exposure: Exposure, max_conc: float = 0.5) -> bool:
    return exposure.concentration > max_conc or exposure.corr_risk_flag


def optimize_allocation(
    returns: pd.DataFrame,
    *,
    method: OptimizationMethod = "mean_risk",
    position_caps: Mapping[str, float] | None = None,
    constraints: Mapping[str, Any] | None = None,
    account_id: str = "default",
    risk_measure: str = "CVaR",
    instruments: Sequence[str] | None = None,
    export_json: bool = True,
    output_dir: Path | str | None = None,
) -> PortfolioOptimizationResult:
    """Run portfolio optimization with per-instrument caps passed to riskfolio_adapter."""
    from pathlib import Path as _Path

    merged_constraints = build_constraints(position_caps, constraints)
    return optimize_portfolio(
        returns,
        method=method,
        risk_measure=risk_measure,
        instruments=instruments or list(DEFAULT_INSTRUMENTS),
        constraints=merged_constraints,
        account_id=account_id,
        export_json=export_json,
        output_dir=_Path(output_dir) if output_dir else None,
    )