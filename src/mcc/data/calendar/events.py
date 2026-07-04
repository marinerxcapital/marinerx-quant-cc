"""Economic calendar per 02_DATA_LAYER.md.

next_event(instrument, now) , in_event_window(now, pre, post).
Synthetic EIA for CL at Wed 10:30 ET, others.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

NY = ZoneInfo("America/New_York")


def _next_wed_1030(now: datetime) -> datetime:
    ny = now.astimezone(NY) if now.tzinfo else now.replace(tzinfo=NY)
    days_ahead = (2 - ny.weekday()) % 7  # Wed=2
    if days_ahead == 0 and (ny.hour > 10 or (ny.hour == 10 and ny.minute > 30)):
        days_ahead = 7
    next_wed = ny + timedelta(days=days_ahead)
    target = next_wed.replace(hour=10, minute=30, second=0, microsecond=0)
    return target.astimezone(timezone.utc)


EIA_INSTRUMENTS = {"CL", "NG"}


def next_event(instrument: str, now: datetime | None = None) -> dict[str, Any]:
    if now is None:
        now = datetime.now(timezone.utc)
    inst = instrument.upper()
    if inst in EIA_INSTRUMENTS:
        ts = _next_wed_1030(now)
        return {"name": "EIA", "ts_utc": ts, "instrument": inst, "desc": "EIA inventory Wed 10:30 ET"}
    # Fallback generic next 10:30
    base = now.astimezone(NY)
    target = base.replace(hour=10, minute=30, second=0)
    if target <= base:
        target += timedelta(days=1)
    return {"name": "GENERIC_RELEASE", "ts_utc": target.astimezone(timezone.utc), "instrument": inst}


def _in_window_bool(delta: timedelta, pre_min: int, post_min: int) -> bool:
    secs = delta.total_seconds()
    return - (pre_min * 60) <= secs <= (post_min * 60)


def in_event_window(now: datetime, pre_min: int = 5, post_min: int = 30) -> bool:
    """True around EIA or generic release windows. Computes today's release window."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    ny = now.astimezone(NY)
    target_ny = ny.replace(hour=10, minute=30, second=0, microsecond=0)
    ev_ts = target_ny.astimezone(timezone.utc)
    # if now is before today release, use previous? but for demo use this day's
    if target_ny < ny and (ny - target_ny).total_seconds() > (post_min * 60 + 60):
        # far after, use next
        ev_ts = (target_ny + timedelta(days=1)).astimezone(timezone.utc)  # simple
    delta = now - ev_ts
    return _in_window_bool(delta, pre_min, post_min)
