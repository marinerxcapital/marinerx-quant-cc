"""Data provider interfaces with demo and missing-key fallbacks."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any


class MarketDataProvider(ABC):
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, limit: int = 500) -> list[dict[str, Any]]:
        ...


class MacroDataProvider(ABC):
    @abstractmethod
    def get_series(self) -> list[dict[str, Any]]:
        ...


class BrokerProvider(ABC):
    @abstractmethod
    def get_account(self) -> dict[str, Any]:
        ...


class DemoMarketProvider(MarketDataProvider):
    def get_bars(self, symbol: str, timeframe: str, limit: int = 500) -> list[dict[str, Any]]:
        base = 18000.0 if symbol.upper() in ("NQ", "MNQ") else 5300.0
        bars = []
        ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
        for i in range(min(limit, 50)):
            o = base + i * 2
            c = o + (4 if i % 3 else -3)
            bars.append({
                "symbol": symbol, "timeframe": timeframe,
                "timestamp": ts + timedelta(minutes=15 * i),
                "open": o, "high": max(o, c) + 5, "low": min(o, c) - 5,
                "close": c, "volume": 1000 + i * 10,
                "source": "DEMO_DATA",
            })
        return bars


class FredMacroProvider(MacroDataProvider):
    def get_series(self) -> list[dict[str, Any]]:
        key = os.environ.get("FRED_API_KEY", "").strip()
        if not key:
            return [{"status": "missing_key", "message": "FRED_API_KEY not configured", "labeled": "DEMO_DATA"}]
        return [{"series_id": "DFF", "name": "Fed Funds Rate", "status": "configured", "key_present": True}]


class PaperBrokerProvider(BrokerProvider):
    def get_account(self) -> dict[str, Any]:
        return {
            "mode": "paper",
            "equity": 100000.0,
            "cash": 100000.0,
            "day_pnl": 0.0,
            "labeled": "SIMULATED",
        }