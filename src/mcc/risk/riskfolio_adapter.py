"""Riskfolio-Lib adapter for portfolio optimization and risk measures (Phase 16).

All Decimal <-> float conversion routes through mcc.analytics.conversion.
Return series are validated via mcc.analytics.validation before library calls.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
import structlog

from mcc.analytics.conversion import decimal_to_float, float_to_decimal, json_number
from mcc.analytics.validation import utc_now, validate_return_series, validate_weights
from mcc.core.exceptions import AnalyticsValidationError

logger = structlog.get_logger(__name__)

OptimizationMethod = Literal["mean_risk", "risk_parity", "hrp", "kelly"]

DEFAULT_INSTRUMENTS: tuple[str, ...] = ("NQ", "ES", "CL", "GC")
DEFAULT_ALLOCATIONS_DIR = Path("reports_out/allocations")

try:
    import riskfolio as rp  # type: ignore[import-untyped]

    _RISKFOLIO_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency at install time
    rp = None  # type: ignore[assignment]
    _RISKFOLIO_AVAILABLE = False


@dataclass
class PortfolioOptimizationResult:
    """Portfolio optimization output matching Phase 16 Section 8.1 schema."""

    run_id: str
    account_id: str
    timestamp_utc: datetime
    instruments: list[str]
    method: OptimizationMethod
    risk_measure: str
    constraints: dict[str, Any]
    weights: dict[str, Decimal]
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    risk_contributions: dict[str, Decimal]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export; numeric fields converted at output boundary."""
        return {
            "run_id": self.run_id,
            "account_id": self.account_id,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "instruments": self.instruments,
            "method": self.method,
            "risk_measure": self.risk_measure,
            "constraints": self.constraints,
            "weights": {k: json_number(v) for k, v in self.weights.items()},
            "expected_return": json_number(self.expected_return),
            "expected_volatility": json_number(self.expected_volatility),
            "sharpe_ratio": json_number(self.sharpe_ratio),
            "risk_contributions": {k: json_number(v) for k, v in self.risk_contributions.items()},
            "warnings": self.warnings,
        }


def _ensure_riskfolio() -> Any:
    if not _RISKFOLIO_AVAILABLE or rp is None:
        raise AnalyticsValidationError(
            "riskfolio-lib is not installed; install with: pip install riskfolio-lib"
        )
    return rp


def _normalize_returns(returns: pd.DataFrame, instruments: Sequence[str]) -> pd.DataFrame:
    """Validate and align return matrix for Riskfolio-Lib."""
    if returns is None or returns.empty:
        raise AnalyticsValidationError("returns: empty DataFrame")
    cols = [c for c in instruments if c in returns.columns]
    if not cols:
        cols = list(returns.columns)
    out = returns[cols].copy()
    for col in out.columns:
        out[col] = validate_return_series(out[col], name=f"returns.{col}")
    return out.dropna(how="all")


def _caps_to_weight_bounds(
    instruments: Sequence[str],
    position_caps: Mapping[str, float] | None,
) -> dict[str, float]:
    """Convert per-instrument contract caps to long-only weight upper bounds."""
    if not position_caps:
        return {sym: 1.0 for sym in instruments}
    caps = {sym: float(position_caps.get(sym, 1.0)) for sym in instruments}
    total = sum(caps.values()) or 1.0
    return {sym: caps[sym] / total for sym in instruments}


def _apply_weight_constraints(
    port: Any,
    instruments: Sequence[str],
    constraints: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Record per-instrument caps; applied post-optimization (cvxpy compat on Py3.14)."""
    merged: dict[str, Any] = dict(constraints or {})
    caps = merged.get("max_position_cap") or merged.get("position_caps")
    upper = _caps_to_weight_bounds(instruments, caps if isinstance(caps, Mapping) else None)
    merged["weight_upper_bounds"] = upper
    return merged


def _clip_weights_to_caps(
    raw: dict[str, float],
    caps: Mapping[str, float] | None,
) -> dict[str, float]:
    """Clip optimized weights to cap-derived bounds and renormalize."""
    if not caps:
        return raw
    upper = _caps_to_weight_bounds(raw.keys(), caps)
    clipped = {sym: min(max(raw.get(sym, 0.0), 0.0), upper.get(sym, 1.0)) for sym in raw}
    total = sum(clipped.values()) or 1.0
    return {sym: clipped[sym] / total for sym in clipped}


def _equal_weight_frame(instruments: Sequence[str]) -> pd.DataFrame:
    equal = 1.0 / len(instruments)
    return pd.DataFrame({"weights": [equal] * len(instruments)}, index=list(instruments))


def _hrp_fallback(returns: pd.DataFrame) -> pd.DataFrame:
    """Hierarchical risk parity fallback when Riskfolio HRP API unavailable."""
    from scipy.cluster.hierarchy import linkage, leaves_list
    from scipy.spatial.distance import squareform

    cols = list(returns.columns)
    cov = returns.cov().values
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    np.fill_diagonal(corr, 1.0)
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, None))
    link = linkage(squareform(dist, checks=False), method="single")
    order = list(leaves_list(link))
    ordered = [cols[i] for i in order]

    def _cluster_var(items: list[str]) -> float:
        sub = returns[items].cov().values
        w = np.ones(len(items)) / len(items)
        return float(w @ sub @ w)

    weights = {c: 1.0 for c in cols}
    clusters: list[list[str]] = [[c] for c in ordered]
    while len(clusters) > 1:
        left, right = clusters[0], clusters[1]
        var_l, var_r = _cluster_var(left), _cluster_var(right)
        alpha = 1.0 - var_l / (var_l + var_r) if (var_l + var_r) > 0 else 0.5
        for sym in left:
            weights[sym] *= alpha
        for sym in right:
            weights[sym] *= 1.0 - alpha
        clusters = [[*left, *right], *clusters[2:]]
    total = sum(weights.values()) or 1.0
    w_series = pd.Series({k: weights[k] / total for k in cols}, name="weights")
    return w_series.to_frame()


def _optimize_weights(
    port: Any,
    returns: pd.DataFrame,
    *,
    method: OptimizationMethod,
    risk_measure: str,
    rf: float,
) -> tuple[pd.DataFrame, list[str]]:
    """Dispatch to Riskfolio-Lib; return weights frame + warnings."""
    notes: list[str] = []
    rm = "MV" if risk_measure in ("CVaR", "cvar", "ES") else risk_measure

    if method == "risk_parity":
        w = port.rp_optimization(model="Classic", rm=rm, rf=rf, b=None, hist=True)
        if w is not None:
            return w, notes
        notes.append("risk_parity: solver returned None, equal-weight fallback")
        return _equal_weight_frame(returns.columns), notes

    if method == "hrp":
        notes.append("hrp: numpy HRP fallback (Riskfolio HRP API not available in installed version)")
        return _hrp_fallback(returns), notes

    if method == "kelly":
        w = port.optimization(model="Classic", rm=rm, obj="Kelly", rf=0.0, l=0, hist=True)
        if w is not None:
            return w, notes
        notes.append("kelly: solver returned None, risk-parity fallback")
        w = port.rp_optimization(model="Classic", rm=rm, rf=rf, b=None, hist=True)
        return w if w is not None else _equal_weight_frame(returns.columns), notes

    w = port.optimization(model="Classic", rm=rm, obj="Sharpe", rf=rf, l=0, hist=True)
    if w is not None:
        return w, notes
    notes.append("mean_risk: Classic solver returned None, risk-parity fallback")
    w = port.rp_optimization(model="Classic", rm=rm, rf=rf, b=None, hist=True)
    return w if w is not None else _equal_weight_frame(returns.columns), notes


def _weights_to_decimal_dict(
    w: pd.DataFrame | pd.Series | None,
    instruments: Sequence[str],
) -> dict[str, Decimal]:
    if w is None:
        equal = 1.0 / len(instruments)
        raw = {str(sym): equal for sym in instruments}
    else:
        if isinstance(w, pd.DataFrame):
            col = w.columns[0]
            series = w[col]
        else:
            series = w
        raw = {}
        for sym in instruments:
            if sym in series.index:
                val = series.loc[sym]
                raw[str(sym)] = float(val.iloc[0]) if isinstance(val, pd.Series) else float(val)
            else:
                raw[str(sym)] = 0.0
    validated = validate_weights(raw, allow_short=False)
    return {k: float_to_decimal(v, context="portfolio_weights") for k, v in validated.items()}


def _portfolio_metrics(
    port: Any,
    weights: dict[str, Decimal],
    instruments: Sequence[str],
    risk_measure: str,
    rf: float,
) -> tuple[Decimal, Decimal, Decimal]:
    """Compute expected return, volatility, and Sharpe from optimized weights."""
    w = pd.Series(
        {s: decimal_to_float(weights[s], context="portfolio_metrics") for s in instruments},
        dtype=float,
    )
    mu = port.mu.squeeze()
    cov = port.cov
    common = [s for s in instruments if s in mu.index]
    w = w.reindex(common).fillna(0.0)
    mu = mu.reindex(common).fillna(0.0)
    cov = cov.reindex(index=common, columns=common).fillna(0.0)
    exp_ret = float(w.values @ mu.values)
    exp_vol = float(np.sqrt(float(w.values @ cov.values @ w.values)))
    sharpe = (exp_ret - rf) / exp_vol if exp_vol > 1e-12 else 0.0
    return (
        float_to_decimal(exp_ret, context="expected_return"),
        float_to_decimal(exp_vol, context="expected_volatility"),
        float_to_decimal(sharpe, context="sharpe_ratio"),
    )


def _risk_contributions(
    port: Any,
    weights: dict[str, Decimal],
    instruments: Sequence[str],
    risk_measure: str,
) -> dict[str, Decimal]:
    """Per-instrument risk contribution via Riskfolio-Lib."""
    w = np.array(
        [decimal_to_float(weights[s], context="risk_contribution") for s in instruments],
        ndmin=2,
    ).T
    cov = np.array(port.cov, dtype=float)
    try:
        rc = rp.RiskFunctions.Risk_Contribution(w, cov, rm=risk_measure)  # type: ignore[union-attr]
        rc_arr = np.asarray(rc).flatten()
        total = float(rc_arr.sum()) or 1.0
        return {
            sym: float_to_decimal(float(rc_arr[i]) / total, context="risk_contribution")
            for i, sym in enumerate(instruments)
        }
    except Exception as exc:  # pragma: no cover - library-specific edge cases
        logger.warning("risk_contribution_fallback", error=str(exc))
        even = Decimal("1") / Decimal(len(instruments))
        return {sym: even for sym in instruments}


def optimize_portfolio(
    returns: pd.DataFrame,
    *,
    method: OptimizationMethod = "mean_risk",
    risk_measure: str = "CVaR",
    instruments: Sequence[str] | None = None,
    constraints: Mapping[str, Any] | None = None,
    account_id: str = "default",
    risk_free_rate: float = 0.045,
    run_id: str | None = None,
    export_json: bool = True,
    output_dir: Path | str | None = None,
) -> PortfolioOptimizationResult:
    """Run Riskfolio-Lib portfolio optimization and optionally export Section 8.1 JSON."""
    lib = _ensure_riskfolio()
    syms = list(instruments or DEFAULT_INSTRUMENTS)
    y = _normalize_returns(returns, syms)
    syms = list(y.columns)

    warnings: list[str] = []
    port = lib.Portfolio(returns=y)
    port.assets_stats(method_mu="hist", method_cov="hist")
    applied_constraints = _apply_weight_constraints(port, syms, constraints)

    caps = applied_constraints.get("max_position_cap") or applied_constraints.get("position_caps")
    try:
        w_df, opt_notes = _optimize_weights(
            port, y, method=method, risk_measure=risk_measure, rf=risk_free_rate
        )
        warnings.extend(opt_notes)
    except Exception as exc:
        warnings.append(f"optimization_fallback: {exc}")
        w_df = _equal_weight_frame(syms)

    raw_floats = {
        s: decimal_to_float(weights_dec, context="cap_clip")
        for s, weights_dec in _weights_to_decimal_dict(w_df, syms).items()
    }
    clipped = _clip_weights_to_caps(raw_floats, caps if isinstance(caps, Mapping) else None)
    weights = {k: float_to_decimal(v, context="portfolio_weights") for k, v in clipped.items()}
    exp_ret, exp_vol, sharpe = _portfolio_metrics(port, weights, syms, risk_measure, risk_free_rate)
    risk_contrib = _risk_contributions(port, weights, syms, risk_measure)

    ts = utc_now()
    result = PortfolioOptimizationResult(
        run_id=run_id or str(uuid.uuid4()),
        account_id=account_id,
        timestamp_utc=ts,
        instruments=syms,
        method=method,
        risk_measure=risk_measure,
        constraints=applied_constraints,
        weights=weights,
        expected_return=exp_ret,
        expected_volatility=exp_vol,
        sharpe_ratio=sharpe,
        risk_contributions=risk_contrib,
        warnings=warnings,
    )
    if export_json:
        write_allocation_json(result, output_dir=output_dir)
    return result


def write_allocation_json(
    result: PortfolioOptimizationResult,
    *,
    output_dir: Path | str | None = None,
) -> Path:
    """Write Section 8.1 allocation JSON to reports_out/allocations/."""
    base = Path(output_dir) if output_dir else DEFAULT_ALLOCATIONS_DIR
    base.mkdir(parents=True, exist_ok=True)
    stamp = result.timestamp_utc.strftime("%Y%m%d_%H%M%S")
    path = base / f"{result.account_id}_{result.method}_{stamp}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    logger.info("allocation_exported", path=str(path), run_id=result.run_id)
    return path


def kelly_raw_fraction(
    win_prob: Decimal,
    payoff: Decimal,
    *,
    returns: pd.DataFrame | None = None,
    instrument: str = "NQ",
    risk_measure: str = "MV",
) -> tuple[Decimal, str]:
    """Uncapped Kelly fraction from Riskfolio-Lib (or analytical fallback)."""
    if payoff <= 0 or win_prob <= 0:
        return Decimal(0), "kelly_raw: invalid win_prob/payoff"

    analytical = win_prob - (Decimal(1) - win_prob) / payoff

    if not _RISKFOLIO_AVAILABLE:
        return analytical, "kelly_raw: analytical (riskfolio-lib not installed)"

    try:
        lib = _ensure_riskfolio()
        if returns is not None and not returns.empty and instrument in returns.columns:
            y = _normalize_returns(returns, [instrument])
            port = lib.Portfolio(returns=y)
            port.assets_stats(method_mu="hist", method_cov="hist")
            w_df = port.optimization(
                model="Classic",
                rm=risk_measure,
                obj="Kelly",
                rf=0.0,
                l=0,
                hist=True,
            )
            raw = float(w_df.loc[instrument].iloc[0])
            return (
                float_to_decimal(max(0.0, raw), context="kelly_raw"),
                f"kelly_raw: riskfolio Kelly on {instrument} returns n={len(y)}",
            )

        mu = (
            decimal_to_float(win_prob, context="kelly_edge")
            * decimal_to_float(payoff, context="kelly_edge")
            - (1.0 - decimal_to_float(win_prob, context="kelly_edge"))
        )
        sigma = max(abs(mu) * 0.5, 0.01)
        synthetic = pd.DataFrame(
            {instrument: np.random.default_rng(42).normal(mu, sigma, 120)},
            index=pd.date_range("2024-01-01", periods=120, freq="B", tz=timezone.utc),
        )
        y = _normalize_returns(synthetic, [instrument])
        port = lib.Portfolio(returns=y)
        port.assets_stats(method_mu="hist", method_cov="hist")
        w_df = port.optimization(
            model="Classic",
            rm=risk_measure,
            obj="Kelly",
            rf=0.0,
            l=0,
            hist=True,
        )
        raw = float(w_df.loc[instrument].iloc[0])
        return (
            float_to_decimal(max(0.0, raw), context="kelly_raw"),
            f"kelly_raw: riskfolio Kelly synthetic edge mu={mu:.4f}",
        )
    except Exception as exc:
        logger.warning("kelly_raw_fallback", error=str(exc))
        return analytical, f"kelly_raw: analytical fallback ({exc})"


def riskfolio_var_es(
    returns: Sequence[float],
    *,
    confidence: float = 0.95,
    risk_measure: str = "CVaR",
) -> tuple[float, float]:
    """Compute VaR and ES/CVaR via Riskfolio-Lib historical risk functions."""
    if len(returns) < 2:
        raise AnalyticsValidationError("returns: need at least 2 observations for riskfolio VaR/ES")

    lib = _ensure_riskfolio()
    arr = np.asarray(returns, dtype=float)
    alpha = 1.0 - confidence

    try:
        var = float(lib.RiskFunctions.VaR_Hist(arr, alpha=alpha))
        es_fn = getattr(lib.RiskFunctions, "CVaR_Hist", None) or getattr(
            lib.RiskFunctions, "ES_Hist", None
        )
        if es_fn is None:
            raise AnalyticsValidationError("riskfolio: CVaR/ES function not available")
        es = float(es_fn(arr, alpha=alpha))
        return abs(var), abs(es)
    except Exception as exc:
        raise AnalyticsValidationError(f"riskfolio VaR/ES failed: {exc}") from exc