"""VaR / ES (historical simulation) + limit breach for Phase 08.

- Historical simulation VaR/ES across positions.
- Optional Riskfolio-Lib CVaR path via riskfolio_adapter.
- Rolling estimation stub (use provided returns).
- Current VaR/ES vs configured limits; breach flag.
- Pure numpy + stdlib for portability (historical path).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

from mcc.risk.riskfolio_adapter import riskfolio_var_es


@dataclass(frozen=True)
class VaRResult:
    var: float
    es: float  # CVaR / Expected Shortfall
    confidence: float
    n_samples: int
    breach: bool
    limit_var: float
    limit_es: float
    reason: str


def historical_var_es(
    returns: Sequence[float],
    confidence: float = 0.95,
    limit_var: float = 0.02,  # 2% portfolio VaR limit example
    limit_es: float = 0.03,
    *,
    use_riskfolio: bool = False,
    risk_measure: str = "CVaR",
) -> VaRResult:
    """Compute historical VaR and ES (CVaR) at given confidence.

    returns: sequence of period returns e.g. daily pnl/equity (can be negative for loss).
    VaR here is the loss quantile (positive number means loss threshold).
    ES is average loss beyond VaR.

    When use_riskfolio=True, delegates to riskfolio_adapter.riskfolio_var_es with
    historical numpy fallback on failure.
    """
    if len(returns) < 5:
        returns = list(returns) + [-0.01] * (10 - len(returns))
    arr = np.asarray(returns, dtype=float)
    if arr.size == 0:
        arr = np.array([-0.005, -0.01, 0.0, 0.005, -0.015])

    method_tag = "hist"
    var = 0.0
    es = 0.0

    if use_riskfolio:
        try:
            var, es = riskfolio_var_es(list(arr), confidence=confidence, risk_measure=risk_measure)
            method_tag = f"riskfolio_{risk_measure.lower()}"
        except Exception:
            method_tag = "hist_fallback"

    if not use_riskfolio or method_tag == "hist_fallback":
        q = 1.0 - confidence
        var_q = float(np.quantile(arr, q))
        var = -var_q
        tail = arr[arr <= var_q]
        if len(tail) == 0:
            es = var
        else:
            es = -float(np.mean(tail))

    breach = (var > limit_var) or (es > limit_es)
    reason = (
        f"{method_tag}_var_es@ {confidence*100:.1f}%: VaR={var:.4f} (limit {limit_var:.4f}) "
        f"ES={es:.4f} (limit {limit_es:.4f}) n={len(arr)} breach={breach}"
    )
    return VaRResult(
        var=var,
        es=es,
        confidence=confidence,
        n_samples=len(arr),
        breach=breach,
        limit_var=limit_var,
        limit_es=limit_es,
        reason=reason,
    )


def var_es_from_pnl_series(
    pnl_series: Sequence[float],
    equity: float,
    confidence: float = 0.95,
    var_limit_pct: float = 0.02,
    es_limit_pct: float = 0.03,
    *,
    use_riskfolio: bool = False,
    risk_measure: str = "CVaR",
) -> VaRResult:
    """Convenience: convert absolute P&L series to returns, run VaR/ES."""
    if equity <= 0:
        equity = 100000.0
    rets = [float(p) / equity for p in pnl_series]
    return historical_var_es(
        rets,
        confidence=confidence,
        limit_var=var_limit_pct,
        limit_es=es_limit_pct,
        use_riskfolio=use_riskfolio,
        risk_measure=risk_measure,
    )


def check_var_es_breach(result: VaRResult) -> bool:
    """Return True if either VaR or ES breaches configured limits."""
    return result.breach


def demo_historical_fixture() -> Tuple[List[float], VaRResult]:
    """Returns (pnl_like_returns, computed_result) for hand-calc verification."""
    rets = [-0.005, -0.012, -0.003, 0.004, -0.008, -0.02, 0.001, -0.007, 0.01, -0.015]
    res = historical_var_es(rets, confidence=0.95, limit_var=0.015, limit_es=0.025)
    return rets, res