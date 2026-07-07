"""Incremental indicator engine — batch/incremental parity for SMA + RSI."""
from __future__ import annotations

from typing import Any

from mcc.indicators.library import compute_rsi, compute_sma, rsi, sma


class IndicatorEngine:
    """Computes SMA/RSI incrementally per instrument from bar closes."""

    def __init__(
        self,
        sma_period: int = 20,
        rsi_period: int = 14,
        max_bars: int = 500,
    ) -> None:
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.max_bars = max_bars
        self._closes: dict[str, list[float]] = {}
        self._last: dict[str, dict[str, float | None]] = {}

    def _close_from_bar(self, bar: dict[str, Any]) -> float:
        return float(bar.get("c", bar.get("close", 0)) or 0)

    def on_bar(self, symbol: str, bar: dict[str, Any]) -> dict[str, float | None]:
        """Incrementally update indicators for one bar; returns latest values."""
        sym = symbol.upper()
        close = self._close_from_bar(bar)
        buf = self._closes.setdefault(sym, [])
        buf.append(close)
        if len(buf) > self.max_bars:
            buf.pop(0)

        values = {
            f"sma{self.sma_period}": sma(buf, self.sma_period),
            f"rsi{self.rsi_period}": rsi(buf, self.rsi_period),
            "close": close,
        }
        self._last[sym] = values
        return values

    def compute_batch(self, symbol: str, closes: list[float]) -> dict[str, list[float | None]]:
        """Batch compute for parity tests."""
        sym = symbol.upper()
        self._closes[sym] = list(closes[-self.max_bars :])
        sma_series = compute_sma(closes, self.sma_period)
        rsi_series = compute_rsi(closes, self.rsi_period)
        self._last[sym] = {
            f"sma{self.sma_period}": sma_series[-1] if sma_series else None,
            f"rsi{self.rsi_period}": rsi_series[-1] if rsi_series else None,
            "close": closes[-1] if closes else None,
        }
        return {
            f"sma{self.sma_period}": sma_series,
            f"rsi{self.rsi_period}": rsi_series,
        }

    def snapshot(self) -> dict[str, Any]:
        return {"instruments": dict(self._last), "config": {"sma": self.sma_period, "rsi": self.rsi_period}}