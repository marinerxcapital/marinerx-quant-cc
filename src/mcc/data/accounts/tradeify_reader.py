"""Read-only Tradeify sync SQLite (WAL) for AccountSync agent."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_account_state(db_path: str | Path) -> dict[str, Any]:
    """Open tradeify_sync.db read-only (WAL-safe) and return latest account state dict.

    Returns empty/stale-shaped dict when file or table is missing.
    """
    path = Path(db_path)
    if not path.exists():
        return {"stale": True, "error": "db_not_found", "path": str(path)}

    uri = f"file:{path.resolve()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                """
                SELECT account_id, balance, equity, drawdown_headroom, daily_pnl,
                       last_synced_utc, phase, status
                FROM accounts
                ORDER BY last_synced_utc DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row is None:
                return {"stale": True, "error": "no_accounts", "path": str(path)}

            data = {k: row[k] for k in row.keys()}
            last_synced = data.get("last_synced_utc")
            stale = _is_stale(last_synced)
            return {
                "type": "account_state",
                "account": data.get("account_id", ""),
                "equity": float(data.get("equity") or data.get("balance") or 0),
                "balance": float(data.get("balance") or 0),
                "drawdown_headroom": float(data.get("drawdown_headroom") or 0),
                "daily_pnl": float(data.get("daily_pnl") or 0),
                "phase": data.get("phase"),
                "status": data.get("status"),
                "last_synced_utc": last_synced,
                "stale": stale,
                "source": "tradeify_reader",
                "path": str(path),
            }
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return {"stale": True, "error": str(exc), "path": str(path)}


def _is_stale(last_synced: Any, max_age_sec: float = 3600.0) -> bool:
    if last_synced is None:
        return True
    try:
        if isinstance(last_synced, (int, float)):
            ts = datetime.fromtimestamp(last_synced, tz=timezone.utc)
        else:
            text = str(last_synced).replace("Z", "+00:00")
            ts = datetime.fromisoformat(text)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age > max_age_sec
    except (ValueError, TypeError, OSError):
        return True