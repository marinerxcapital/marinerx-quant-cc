"""Replay adapter (default for no keys) per 02_DATA_LAYER.md.

Streams historical (synthetic cached) bars through bus at configurable speed (e.g. 60x)
using SimClock. Implements LiveFeed protocol surface so consumers unchanged when swapping adapters.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import AsyncIterator, Sequence

import pandas as pd

from mcc.core.bus import MessageBus
from mcc.core.clock import SimClock, Clock
from mcc.core.events import BarEvent, Topic


class ReplayAdapter:
    """Replay adapter: plays back bars (from parquet or synthetic) as events at speed factor."""

    def __init__(self, bus: MessageBus | None = None, clock: Clock | None = None, speed: float = 60.0, data_dir: Path | str = "data/catalog") -> None:
        self.bus = bus or MessageBus()
        self.clock: Clock = clock or SimClock()
        self.speed = speed
        self.data_dir = Path(data_dir)
        self._bars: pd.DataFrame | None = None
        self._connected = False
        self.symbols: list[str] = []
        self.channels: list[str] = []

    async def connect(self) -> None:
        self._connected = True

    async def subscribe(self, symbols: Sequence[str], channels: Sequence[str]) -> None:
        self.symbols = list(symbols)
        self.channels = list(channels)

    def _load_or_synth(self, symbol: str = "NQ", n_bars: int = 390) -> pd.DataFrame:
        """Load cached parquet or synthesize a trading day of 1-min bars (RTH approx)."""
        p = self.data_dir / f"bars_{symbol}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            if "ts" not in df.columns:
                df = df.reset_index()
            return df.head(n_bars)
        # Synthesize
        start = datetime(2024, 1, 2, 9, 30, tzinfo=timezone.utc)
        rows = []
        price = 15000.0
        for i in range(n_bars):
            ts = start + timedelta(minutes=i)
            o = price
            c = price + (i % 5 - 2) * 0.5
            h = max(o, c) + 0.25
            lo = min(o, c) - 0.25
            v = 100 + (i % 10) * 20
            rows.append({"ts": ts, "symbol": symbol, "o": o, "h": h, "l": lo, "c": c, "v": v})
            price = c
        df = pd.DataFrame(rows)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, index=False)
        return df

    async def stream(self) -> AsyncIterator[BarEvent]:
        """Yield BarEvents at accelerated rate. SimClock advanced accordingly."""
        if not isinstance(self.clock, SimClock):
            # wrap
            self.clock = SimClock()
        sim: SimClock = self.clock if isinstance(self.clock, SimClock) else SimClock()


        sim.set_speed(self.speed)

        df = self._bars if self._bars is not None else self._load_or_synth(self.symbols[0] if self.symbols else "NQ")
        self._bars = df

        base_t = None
        for _, row in df.iterrows():
            if "ts" in row:
                ts = pd.to_datetime(row["ts"]).to_pydatetime()
            else:
                ts = datetime.now(timezone.utc)
            if base_t is None:
                base_t = ts
                sim.set(ts)
            # advance sim clock proportionally (for 60x, sleep is 1/60)
            ev = BarEvent(
                topic=Topic.BARS,
                ts_utc=ts,
                source="replay",
                payload={
                    "symbol": row.get("symbol", "NQ"),
                    "o": float(row.get("o", row.get("c", 0))),
                    "h": float(row.get("h", row.get("c", 0))),
                    "l": float(row.get("l", row.get("c", 0))),
                    "c": float(row.get("c", 0)),
                    "v": int(row.get("v", 0)),
                },
            )
            await self.bus.publish(ev)
            yield ev

            # playback timing: wall sleep reduced by speed; advance sim
            real_sleep = 1.0 / max(self.speed, 0.1)  # seconds per bar at speed
            await asyncio.sleep(real_sleep)
            sim.advance(timedelta(minutes=1))

    async def disconnect(self) -> None:
        self._connected = False

    # Convenience for tests: count streamed without full consume timing
    async def stream_and_count(self, limit: int | None = None) -> int:
        cnt = 0
        async for _ in self.stream():
            cnt += 1
            if limit and cnt >= limit:
                break
        return cnt
