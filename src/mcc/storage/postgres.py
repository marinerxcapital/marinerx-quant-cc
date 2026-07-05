"""Postgres connectivity helpers."""
from __future__ import annotations

from typing import Any

from mcc.storage.database import check_database_connectivity, get_engine


def validate_postgres_url(database_url: str) -> dict[str, Any]:
    if not database_url.startswith("postgresql"):
        return {"status": "error", "error": "DATABASE_URL must use postgresql scheme"}
    return check_database_connectivity(database_url)


def is_postgres_engine() -> bool:
    eng = get_engine()
    return str(eng.url).startswith("postgresql")