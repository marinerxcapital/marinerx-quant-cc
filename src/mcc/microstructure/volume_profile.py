"""Session volume profile — POC / value area from bar volume."""
from __future__ import annotations

from typing import Any


def build_volume_profile(bars: list[dict[str, Any]], *, bins: int = 12) -> dict[str, Any] | None:
    if not bars:
        return None

    lows = [float(b.get("low", b.get("l", 0)) or 0) for b in bars]
    highs = [float(b.get("high", b.get("h", 0)) or 0) for b in bars]
    vols = [float(b.get("volume", b.get("v", 0)) or 0) for b in bars]
    if not lows or max(highs) <= min(lows):
        return None

    lo = min(lows)
    hi = max(highs)
    step = (hi - lo) / bins if hi > lo else 1.0
    hist = [0.0] * bins
    for bar in bars:
        low = float(bar.get("low", bar.get("l", lo)) or lo)
        high = float(bar.get("high", bar.get("h", hi)) or hi)
        vol = float(bar.get("volume", bar.get("v", 0)) or 0)
        mid = (low + high) / 2.0
        idx = min(bins - 1, max(0, int((mid - lo) / step))) if step else 0
        hist[idx] += vol

    poc_idx = max(range(bins), key=lambda i: hist[i])
    poc = round(lo + (poc_idx + 0.5) * step, 2)
    total = sum(hist) or 1.0
    target = total * 0.7
    acc = hist[poc_idx]
    left, right = poc_idx - 1, poc_idx + 1
    va_indices = {poc_idx}
    while acc < target and (left >= 0 or right < bins):
        left_vol = hist[left] if left >= 0 else -1.0
        right_vol = hist[right] if right < bins else -1.0
        if right_vol >= left_vol and right < bins:
            va_indices.add(right)
            acc += hist[right]
            right += 1
        elif left >= 0:
            va_indices.add(left)
            acc += hist[left]
            left -= 1
        else:
            break

    val = round(lo + min(va_indices) * step, 2)
    vah = round(lo + (max(va_indices) + 1) * step, 2)
    price_labels = [round(lo + (i + 0.5) * step, 2) for i in range(bins)]

    return {
        "poc": poc,
        "vah": vah,
        "val": val,
        "bins": bins,
        "volume_by_price": [round(v, 1) for v in hist],
        "price_labels": price_labels,
    }