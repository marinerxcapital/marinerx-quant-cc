"""Timezone-aware timestamp parsing and canonicalization."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

_EPOCH_MS_THRESHOLD = 1_000_000_000_000
_DASHBOARD_FMT = "%m/%d/%Y %H:%M:%S"
_ISO_FMT = "%Y-%m-%dT%H:%M:%S"


def to_utc(dt_or_str: datetime | str | int | float, display_tz: str = "America/New_York") -> datetime:
    """Convert a datetime, string, or epoch value to tz-aware UTC."""
    if isinstance(dt_or_str, datetime):
        if dt_or_str.tzinfo is None:
            local = ZoneInfo(display_tz)
            return dt_or_str.replace(tzinfo=local).astimezone(UTC)
        return dt_or_str.astimezone(UTC)

    if isinstance(dt_or_str, (int, float)):
        if dt_or_str > _EPOCH_MS_THRESHOLD:
            dt_or_str = dt_or_str / 1000.0
        return datetime.fromtimestamp(dt_or_str, tz=UTC)

    raw = str(dt_or_str).strip()
    if not raw:
        raise ValueError("Empty timestamp")

    if raw.endswith("Z"):
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)

    if re.match(r"^\d{10,13}$", raw):
        val = int(raw)
        if val > _EPOCH_MS_THRESHOLD:
            val = val // 1000
        return datetime.fromtimestamp(val, tz=UTC)

    local = ZoneInfo(display_tz)
    for fmt in (_DASHBOARD_FMT, _ISO_FMT, "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            naive = datetime.strptime(raw, fmt)
            return naive.replace(tzinfo=local).astimezone(UTC)
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=local).astimezone(UTC)
        return parsed.astimezone(UTC)
    except ValueError as exc:
        raise ValueError(f"Unparseable timestamp: {raw}") from exc


def parse_dashboard_timestamp(raw: str, display_tz: str = "America/New_York") -> datetime:
    """Parse a dashboard timestamp string to UTC."""
    return to_utc(raw, display_tz)


def canonical_iso(dt: datetime) -> str:
    """Return a canonical ISO string for hashing (UTC, no microseconds)."""
    utc = dt.astimezone(UTC).replace(microsecond=0)
    return utc.isoformat().replace("+00:00", "Z")