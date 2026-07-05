"""Backward-compatible relational storage facade."""
from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Engine

from mcc.storage.database import check_database_connectivity, get_engine, init_db
from mcc.storage.models import AccountState, Base, Strategy, Trade

__all__ = [
    "Base",
    "Strategy",
    "AccountState",
    "Trade",
    "init_db",
    "get_engine",
    "check_database_connectivity",
]