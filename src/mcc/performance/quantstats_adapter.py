"""QuantStats adapter — trade blotter to return series, metrics, tearsheets (Phase 16)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Final, TypedDict

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import quantstats as qs

from mcc.analytics.conversion import float_to_decimal, json_number
from mcc.analytics.validation import validate_return_series

DEFAULT_BENCHMARK_LABEL: Final[str] = "flat_rate_4.5pct"
DEFAULT_RISK_FREE_ANNUAL: Final[float] = 0.045
TRADING_DAYS_PER_YEAR: Final[int] = 252

# FIXTURE constants — tests only
FIXTURE_STRATEGY_ID: Final[str] = "STR-FIXTURE-001"
FIXTURE_STARTING_EQUITY: Final[float] = 100_000.0


class PerformanceMetricsReport(TypedDict):
    """Section 8.2 Performance Analytics Report schema."""

    strategy_id_or_account_id: str
    benchmark: str
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    sharpe: float
    sortino: float
    calmar: float
    report_path: str


def _parse_trade_timestamp(trade: dict[str, Any], *keys: str) -> pd.Timestamp | None:
    for key in keys:
        raw = trade.get(key)
        if raw is None:
            continue
        if isinstance(raw, datetime):
            ts = pd.Timestamp(raw)
        else:
            ts = pd.Timestamp(str(raw))
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        return ts
    return None


def _trade_return(trade: dict[str, Any], starting_equity: float) -> float:
    """Derive per-trade return from pnl or explicit return_pct."""
    if "return_pct" in trade and trade["return_pct"] is not None:
        return float(trade["return_pct"])
    pnl = trade.get("pnl")
    if pnl is None:
        return 0.0
    notional = trade.get("notional") or trade.get("equity_at_exit") or starting_equity
    denom = float(notional) if float(notional) > 0 else starting_equity
    return float(pnl) / denom


def trades_to_return_series(
    trades: list[dict[str, Any]],
    *,
    starting_equity: float = FIXTURE_STARTING_EQUITY,
    freq: str = "D",
) -> pd.Series:
    """Convert round-turn trade blotter rows into a daily return series.

    Each trade is expected to carry an exit timestamp (``exit_ts`` or ``ts_utc``)
    and either ``return_pct`` or ``pnl`` (optionally ``notional`` / ``equity_at_exit``).

    Returns are aggregated by calendar day (last write wins for duplicate days when
    summing intraday round-turns).
    """
    if not trades:
        raise ValueError("trades: empty blotter")

    rows: list[tuple[pd.Timestamp, float]] = []
    for trade in trades:
        ts = _parse_trade_timestamp(trade, "exit_ts", "close_ts", "ts_utc", "ts")
        if ts is None:
            continue
        ret = _trade_return(trade, starting_equity)
        rows.append((ts, ret))

    if not rows:
        raise ValueError("trades: no rows with parseable exit timestamps")

    df = pd.DataFrame(rows, columns=["ts", "return"])
    df = df.set_index("ts").sort_index()
    daily = df["return"].resample(freq).sum()
    daily.index = pd.DatetimeIndex(daily.index).tz_convert(timezone.utc)
    daily.name = "strategy_returns"
    return validate_return_series(daily, name="trades_daily_returns")


def flat_rate_benchmark_series(
    returns: pd.Series,
    *,
    annual_rate: float = DEFAULT_RISK_FREE_ANNUAL,
    label: str = DEFAULT_BENCHMARK_LABEL,
) -> pd.Series:
    """Build a flat risk-free daily return benchmark aligned to ``returns`` index."""
    _ = label  # label carried in report metadata, not series name
    daily = (1.0 + annual_rate) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
    bench = pd.Series(daily, index=returns.index, name="benchmark")
    return validate_return_series(bench, name="flat_benchmark")


def _safe_metric(fn: Any, *args: Any, default: float = 0.0, **kwargs: Any) -> float:
    try:
        val = fn(*args, **kwargs)
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return default
        return float(val)
    except Exception:
        return default


def compute_metrics(
    returns: pd.Series,
    *,
    strategy_id_or_account_id: str = FIXTURE_STRATEGY_ID,
    benchmark_label: str = DEFAULT_BENCHMARK_LABEL,
    risk_free_annual: float = DEFAULT_RISK_FREE_ANNUAL,
    report_path: str = "",
) -> PerformanceMetricsReport:
    """Compute Section 8.2 metrics via QuantStats on a validated return series.

    Note: Sharpe/Sortino/Calmar are period-return basis (not per-trade), per Phase 16
    API contract documentation.
    """
    validated = validate_return_series(returns, name="performance_returns")
    rf_period = (1.0 + risk_free_annual) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0

    total_return = _safe_metric(qs.stats.comp, validated)
    cagr = _safe_metric(qs.stats.cagr, validated)
    vol = _safe_metric(qs.stats.volatility, validated, annualize=True)
    max_dd = _safe_metric(qs.stats.max_drawdown, validated)
    sharpe = _safe_metric(qs.stats.sharpe, validated, rf=rf_period)
    sortino = _safe_metric(qs.stats.sortino, validated, rf=rf_period)
    calmar = _safe_metric(qs.stats.calmar, validated)

    start = validated.index.min().date()
    end = validated.index.max().date()

    return PerformanceMetricsReport(
        strategy_id_or_account_id=strategy_id_or_account_id,
        benchmark=benchmark_label,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        total_return=json_number(float_to_decimal(total_return, precision=8)),
        annualized_return=json_number(float_to_decimal(cagr, precision=8)),
        annualized_volatility=json_number(float_to_decimal(vol, precision=8)),
        max_drawdown=json_number(float_to_decimal(max_dd, precision=8)),
        sharpe=json_number(float_to_decimal(sharpe, precision=8)),
        sortino=json_number(float_to_decimal(sortino, precision=8)),
        calmar=json_number(float_to_decimal(calmar, precision=8)),
        report_path=report_path,
    )


def _quantstats_safe_series(series: pd.Series) -> pd.Series:
    """Strip tz for QuantStats compatibility (pandas reindex dtype mismatch)."""
    out = series.copy()
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    return out


def generate_tearsheet(
    returns: pd.Series,
    strategy_id: str,
    out_dir: str | Path,
    *,
    benchmark_label: str = DEFAULT_BENCHMARK_LABEL,
    risk_free_annual: float = DEFAULT_RISK_FREE_ANNUAL,
    title: str | None = None,
) -> Path:
    """Generate QuantStats HTML tearsheet; return path to written file.

    Output path: ``{out_dir}/{strategy_id}_{YYYY-MM-DD}.html``
    Benchmark is a flat risk-free rate (``rf``), labeled explicitly in the title — not an equity index.
    """
    validated = validate_return_series(returns, name="tearsheet_returns")
    rf_period = (1.0 + risk_free_annual) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
    qs_returns = _quantstats_safe_series(validated)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    safe_id = strategy_id.replace("/", "_").replace("\\", "_")
    path = out / f"{safe_id}_{stamp}.html"

    display_title = title or f"{strategy_id} vs {benchmark_label} (flat rate, not equity index)"
    qs.reports.html(
        qs_returns,
        benchmark=None,
        rf=rf_period,
        output=str(path),
        title=display_title,
        download_filename=path.name,
    )
    return path


def export_metrics_json(metrics: PerformanceMetricsReport, out_dir: str | Path) -> Path:
    """Write Section 8.2 JSON artifact alongside tearsheet for dashboard consumption."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sid = metrics["strategy_id_or_account_id"].replace("/", "_")
    path = out / f"{sid}_{metrics['end_date']}_metrics.json"
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return path


def fixture_trades() -> list[dict[str, Any]]:
    """Deterministic trade blotter for tests — labeled FIXTURE, not production."""
    base = pd.Timestamp("2024-06-03 15:00", tz="UTC")
    return [
        {"exit_ts": base, "pnl": 250.0, "symbol": "NQ", "strategy_id": FIXTURE_STRATEGY_ID},
        {"exit_ts": base + pd.Timedelta(days=1), "pnl": -120.0, "symbol": "NQ", "strategy_id": FIXTURE_STRATEGY_ID},
        {"exit_ts": base + pd.Timedelta(days=2), "pnl": 400.0, "symbol": "ES", "strategy_id": FIXTURE_STRATEGY_ID},
        {"exit_ts": base + pd.Timedelta(days=3), "pnl": 80.0, "symbol": "CL", "strategy_id": FIXTURE_STRATEGY_ID},
        {"exit_ts": base + pd.Timedelta(days=5), "pnl": -200.0, "symbol": "GC", "strategy_id": FIXTURE_STRATEGY_ID},
    ]