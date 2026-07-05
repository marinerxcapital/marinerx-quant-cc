"""Performance analytics — QuantStats adapter + MCC decision attribution."""
from mcc.performance.analytics import compose_performance_report, decision_attribution
from mcc.performance.quantstats_adapter import (
    DEFAULT_BENCHMARK_LABEL,
    compute_metrics,
    generate_tearsheet,
    trades_to_return_series,
)

__all__ = [
    "DEFAULT_BENCHMARK_LABEL",
    "compute_metrics",
    "compose_performance_report",
    "decision_attribution",
    "generate_tearsheet",
    "trades_to_return_series",
]