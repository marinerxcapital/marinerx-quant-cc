"""Module-level agent snapshot registry for UI and cross-agent reads."""
from __future__ import annotations

from typing import Any

_snapshots: dict[str, dict[str, Any]] = {}


class AgentSnapshotRegistry:
    """Thread-safe-enough in-process registry of per-agent snapshot dicts."""

    @staticmethod
    def set(agent: str, data: dict[str, Any]) -> None:
        _snapshots[agent] = dict(data)

    @staticmethod
    def get(agent: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        return dict(_snapshots.get(agent, default or {}))

    @staticmethod
    def all() -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in _snapshots.items()}

    @staticmethod
    def clear() -> None:
        _snapshots.clear()


# Convenience alias for UI imports
snapshots = _snapshots