"""Clocks per Phase 01/02 spec: Real + Sim for replay/backtests.

CME session helpers (RTH/ETH, America/New_York, DST-aware) minimal.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...


class RealClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SimClock(Clock):
    """Simulated clock for replay. Supports advance and set."""
    def __init__(self, start: datetime | None = None):
        if start is None:
            start = datetime(2024, 1, 2, 9, 30, tzinfo=NY_TZ).astimezone(timezone.utc)
        self._now = start
        self._speed: float = 1.0

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> datetime:
        self._now += delta
        return self._now

    def set(self, t: datetime) -> None:
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        self._now = t

    def set_speed(self, factor: float) -> None:
        self._speed = factor


def is_rth(ts: datetime) -> bool:
    """Rough RTH 9:30-16:00 ET for futures (mon-fri)."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ny = ts.astimezone(NY_TZ)
    if ny.weekday() >= 5:
        return False
    t = ny.time()
    return (t.hour > 9 or (t.hour == 9 and t.minute >= 30)) and t.hour < 16


def session_bounds(ts: datetime) -> tuple[datetime, datetime]:
    """Return (session_open, session_close) in utc for the day."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ny = ts.astimezone(NY_TZ)
    open_ny = datetime(ny.year, ny.month, ny.day, 9, 30, tzinfo=NY_TZ)
    close_ny = datetime(ny.year, ny.month, ny.day, 16, 0, tzinfo=NY_TZ)
    return open_ny.astimezone(timezone.utc), close_ny.astimezone(timezone.utc)
