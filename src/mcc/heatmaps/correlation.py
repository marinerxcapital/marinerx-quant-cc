"""Rolling cross-instrument correlation heatmap from live bar closes."""
from __future__ import annotations

import math
from typing import Any, Callable

from mcc.heatmaps.frame import HeatmapFrame, now_ts


def _pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0
    ax, bx = a[-n:], b[-n:]
    mean_a = sum(ax) / n
    mean_b = sum(bx) / n
    num = sum((ax[i] - mean_a) * (bx[i] - mean_b) for i in range(n))
    den_a = math.sqrt(sum((x - mean_a) ** 2 for x in ax))
    den_b = math.sqrt(sum((x - mean_b) ** 2 for x in bx))
    if den_a == 0 or den_b == 0:
        return 0.0
    return max(-1.0, min(1.0, num / (den_a * den_b)))


def build_correlation_frame(
    symbols: list[str],
    get_bars: Callable[[str], dict[str, Any]],
    *,
    window: int = 20,
) -> HeatmapFrame | None:
    closes: dict[str, list[float]] = {}
    for sym in symbols:
        data = get_bars(sym)
        bars = data.get("bars") or []
        series = [float(b["close"]) for b in bars if b.get("close") is not None]
        if len(series) >= window:
            closes[sym] = series[-window:]

    active = [s for s in symbols if s in closes]
    if len(active) < 2:
        return None

    z: list[list[float]] = []
    for row_sym in active:
        row: list[float] = []
        for col_sym in active:
            if row_sym == col_sym:
                row.append(1.0)
            else:
                row.append(round(_pearson(closes[row_sym], closes[col_sym]), 3))
        z.append(row)

    return HeatmapFrame(
        rows=len(active),
        cols=len(active),
        z=z,
        x_labels=active,
        y_labels=active,
        ts=now_ts(),
        name="correlation",
        source="yfinance_bars",
    )