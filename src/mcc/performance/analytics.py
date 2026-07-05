"""MCC performance analytics — decision attribution composed with QuantStats (Phase 16)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, TypedDict

from mcc.performance.quantstats_adapter import (
    DEFAULT_BENCHMARK_LABEL,
    PerformanceMetricsReport,
    compute_metrics,
    export_metrics_json,
    generate_tearsheet,
    trades_to_return_series,
)

DEFAULT_TEAR_SHEETS_DIR: Final[str] = "reports_out/tear_sheets"


class DecisionAttribution(TypedDict):
    """MCC-specific GO / NO-GO profitability attribution."""

    go_count: int
    go_profitable_count: int
    go_unprofitable_count: int
    go_hit_rate: float
    go_total_pnl: float
    go_avg_pnl: float
    no_go_avoided_loss: float
    no_go_missed_gain: float
    net_attribution_edge: float
    by_setup: dict[str, dict[str, float]]
    by_regime: dict[str, dict[str, float]]


def _trade_pnl(trade: dict[str, Any]) -> float:
    pnl = trade.get("pnl")
    if pnl is not None:
        return float(pnl)
    ret = trade.get("return_pct")
    if ret is not None:
        notional = float(trade.get("notional") or trade.get("equity_at_exit") or 100_000.0)
        return float(ret) * notional
    return 0.0


def _group_attribution(trades: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[float]] = {}
    for t in trades:
        label = str(t.get(key) or "unknown")
        buckets.setdefault(label, []).append(_trade_pnl(t))
    out: dict[str, dict[str, float]] = {}
    for label, pnls in buckets.items():
        wins = [p for p in pnls if p > 0]
        out[label] = {
            "count": float(len(pnls)),
            "total_pnl": float(sum(pnls)),
            "avg_pnl": float(sum(pnls) / len(pnls)) if pnls else 0.0,
            "hit_rate": float(len(wins) / len(pnls)) if pnls else 0.0,
        }
    return out


def decision_attribution(
    go_profitable: list[dict[str, Any]],
    go_unprofitable: list[dict[str, Any]],
    *,
    no_go_avoided: list[dict[str, Any]] | None = None,
    no_go_missed: list[dict[str, Any]] | None = None,
) -> DecisionAttribution:
    """Track whether GO calls were profitable vs NO-GO counterfactuals.

    This is MCC-specific logic preserved alongside QuantStats period-return metrics.
    Counterfactual lists are optional but improve attribution when supplied by the
    decision engine / journal replay.
    """
    avoided = no_go_avoided or []
    missed = no_go_missed or []

    go_all = list(go_profitable) + list(go_unprofitable)
    go_pnls = [_trade_pnl(t) for t in go_all]
    go_wins = [_trade_pnl(t) for t in go_profitable]

    avoided_loss = sum(abs(_trade_pnl(t)) for t in avoided if _trade_pnl(t) < 0)
    missed_gain = sum(_trade_pnl(t) for t in missed if _trade_pnl(t) > 0)
    go_total = float(sum(go_pnls))
    edge = go_total + float(avoided_loss) - float(missed_gain)

    return DecisionAttribution(
        go_count=len(go_all),
        go_profitable_count=len(go_profitable),
        go_unprofitable_count=len(go_unprofitable),
        go_hit_rate=float(len(go_wins) / len(go_all)) if go_all else 0.0,
        go_total_pnl=go_total,
        go_avg_pnl=float(go_total / len(go_all)) if go_all else 0.0,
        no_go_avoided_loss=float(avoided_loss),
        no_go_missed_gain=float(missed_gain),
        net_attribution_edge=float(edge),
        by_setup=_group_attribution(go_all, "setup"),
        by_regime=_group_attribution(go_all, "regime"),
    )


class PerformanceReport(TypedDict):
    """Combined QuantStats metrics + MCC decision attribution."""

    metrics: PerformanceMetricsReport
    attribution: DecisionAttribution
    tearsheet_path: str
    metrics_json_path: str


def compose_performance_report(
    trades: list[dict[str, Any]],
    *,
    strategy_id: str,
    go_profitable: list[dict[str, Any]] | None = None,
    go_unprofitable: list[dict[str, Any]] | None = None,
    no_go_avoided: list[dict[str, Any]] | None = None,
    no_go_missed: list[dict[str, Any]] | None = None,
    out_dir: str | Path = DEFAULT_TEAR_SHEETS_DIR,
    benchmark_label: str = DEFAULT_BENCHMARK_LABEL,
    starting_equity: float = 100_000.0,
    write_combined_json: bool = True,
) -> PerformanceReport:
    """Build full performance package: returns → metrics → tearsheet + attribution."""
    returns = trades_to_return_series(trades, starting_equity=starting_equity)

    tearsheet_path = generate_tearsheet(
        returns,
        strategy_id,
        out_dir,
        benchmark_label=benchmark_label,
    )

    metrics = compute_metrics(
        returns,
        strategy_id_or_account_id=strategy_id,
        benchmark_label=benchmark_label,
        report_path=str(tearsheet_path),
    )
    metrics_json_path = export_metrics_json(metrics, out_dir)

    profitable = go_profitable if go_profitable is not None else [t for t in trades if _trade_pnl(t) > 0]
    unprofitable = go_unprofitable if go_unprofitable is not None else [t for t in trades if _trade_pnl(t) <= 0]
    attribution = decision_attribution(
        profitable,
        unprofitable,
        no_go_avoided=no_go_avoided,
        no_go_missed=no_go_missed,
    )

    if write_combined_json:
        combined_path = Path(out_dir) / f"{strategy_id.replace('/', '_')}_performance_report.json"
        combined_path.write_text(
            json.dumps(
                {
                    "metrics": metrics,
                    "attribution": attribution,
                    "tearsheet_path": str(tearsheet_path),
                    "metrics_json_path": str(metrics_json_path),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return PerformanceReport(
        metrics=metrics,
        attribution=attribution,
        tearsheet_path=str(tearsheet_path),
        metrics_json_path=str(metrics_json_path),
    )