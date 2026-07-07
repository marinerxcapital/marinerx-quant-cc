"""Pure indicator functions — no look-ahead (outputs at t use data <= t)."""
from __future__ import annotations

from typing import Sequence


def sma(values: Sequence[float], period: int) -> float | None:
    """Simple moving average of the last `period` values."""
    if period < 1 or len(values) < period:
        return None
    chunk = values[-period:]
    return sum(chunk) / period


def compute_sma(closes: Sequence[float], period: int) -> list[float | None]:
    """Vectorized SMA series aligned to closes (None during warmup)."""
    out: list[float | None] = []
    for i in range(len(closes)):
        if i + 1 < period:
            out.append(None)
        else:
            out.append(sum(closes[i + 1 - period : i + 1]) / period)
    return out


def rsi(values: Sequence[float], period: int = 14) -> float | None:
    """Wilder RSI on the last `period+1` closes (needs one prior for delta)."""
    if period < 1 or len(values) < period + 1:
        return None
    deltas = [values[i] - values[i - 1] for i in range(len(values) - period, len(values))]
    gains = [max(0.0, d) for d in deltas]
    losses = [max(0.0, -d) for d in deltas]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_rsi(closes: Sequence[float], period: int = 14) -> list[float | None]:
    """Vectorized RSI series (None during warmup)."""
    out: list[float | None] = [None] * len(closes)
    if len(closes) < period + 1:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains.append(max(0.0, d))
        losses.append(max(0.0, -d))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    def _rsi_from_avgs(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        return 100.0 - (100.0 / (1.0 + ag / al))

    out[period] = _rsi_from_avgs(avg_gain, avg_loss)

    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = max(0.0, d)
        l = max(0.0, -d)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        out[i] = _rsi_from_avgs(avg_gain, avg_loss)

    return out