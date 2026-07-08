"""Realized volatility heatmap across instruments and rolling windows."""
from __future__ import annotations

import math
from typing import Any, Callable

from mcc.heatmaps.frame import HeatmapFrame, now_ts

WINDOWS = ("5", "10", "20", "40")


def _realized_vol(closes: list[float], window: int) -> float | None:
    if len(closes) < window + 1:
        return None
    chunk = closes[-(window + 1) :]
    rets = []
    for i in range(1, len(chunk)):
        prev = chunk[i - 1]
        if prev == 0:
            continue
        rets.append((chunk[i] - prev) / prev)
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    return round(math.sqrt(var) * math.sqrt(252) * 100, 3)


def build_volatility_frame(
    symbols: list[str],
    get_bars: Callable[[str], dict[str, Any]],
) -> HeatmapFrame | None:
    labels: list[str] = []
    z_row: list[float] = []
    for sym in symbols:
        data = get_bars(sym)
        bars = data.get("bars") or []
        closes = [float(b["close"]) for b in bars if b.get("close") is not None]
        if len(closes) < 6:
            continue
        labels.append(sym)
        row: list[float] = []
        for w in WINDOWS:
            vol = _realized_vol(closes, int(w))
            row.append(vol if vol is not None else 0.0)
        z_row.append(row)

    if not labels:
        return None

    return HeatmapFrame(
        rows=len(labels),
        cols=len(WINDOWS),
        z=z_row,
        x_labels=list(WINDOWS),
        y_labels=labels,
        ts=now_ts(),
        name="volatility",
        source="yfinance_bars",
    )