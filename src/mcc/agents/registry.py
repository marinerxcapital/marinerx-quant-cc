"""Agent registry (15 named)."""
from __future__ import annotations
from typing import Dict, Type, Optional
from mcc.core.base_agent import BaseAgent

_registry: Dict[str, Type[BaseAgent]] = {}


def register(name: str, cls: Type[BaseAgent]) -> None:
    _registry[name] = cls


def get(name: str) -> Optional[Type[BaseAgent]]:
    return _registry.get(name)


def all_names() -> list[str]:
    return list(_registry.keys())
