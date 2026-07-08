"""Normalized heatmap frame schema for web + TUI."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class HeatmapFrame:
    rows: int
    cols: int
    z: list[list[float]]
    x_labels: list[str]
    y_labels: list[str]
    ts: str
    name: str = "heatmap"
    source: str = "marketpulse"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rows": self.rows,
            "cols": self.cols,
            "z": self.z,
            "x_labels": self.x_labels,
            "y_labels": self.y_labels,
            "ts": self.ts,
            "source": self.source,
        }


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()