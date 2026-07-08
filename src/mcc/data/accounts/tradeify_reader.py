"""Read-only Tradeify sync SQLite (WAL) for AccountSync agent."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def resolve_tradeify_db_path() -> Path | None:
    """Return first existing tradeify_sync.db on the search path."""
    env_path = os.environ.get("TRADEIFY_SYNC_DB_PATH", "").strip()
    if env_path:
        path = Path(env_path)
        return path if path.exists() else None

    candidates: list[Path] = []
    here = Path(__file__).resolve()
    repo_root = here.parents[4]
    candidates.extend(
        [
            repo_root / "tradeify-sync" / "data" / "tradeify_sync.db",
            repo_root / "data" / "tradeify_sync.db",
            Path("tradeify-sync/data/tradeify_sync.db"),
            Path("data/tradeify_sync.db"),
        ]
    )

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return None


def _week_pnl_from_trades(conn: sqlite3.Connection, account_id: str) -> float | None:
    """Sum net_pnl for trades in the rolling 7-day window for the account."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    try:
        cur = conn.execute(
            """
            SELECT net_pnl FROM trades
            WHERE account_id = ? AND exit_time_utc >= ?
            """,
            (account_id, cutoff),
        )
        rows = cur.fetchall()
    except sqlite3.Error:
        return None
    if not rows:
        return None
    total = 0.0
    found = False
    for (net_pnl,) in rows:
        if net_pnl is None:
            continue
        try:
            total += float(net_pnl)
            found = True
        except (TypeError, ValueError):
            continue
    return round(total, 2) if found else None


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
            account_id = str(data.get("account_id") or "")
            week_pnl = _week_pnl_from_trades(conn, account_id) if account_id else None
            daily_raw = data.get("daily_pnl")
            daily_pnl = float(daily_raw) if daily_raw not in (None, "") else None
            balance_raw = data.get("balance")
            equity_raw = data.get("equity")
            headroom_raw = data.get("drawdown_headroom")
            return {
                "type": "account_state",
                "account": account_id,
                "equity": float(equity_raw or balance_raw or 0) if (equity_raw or balance_raw) not in (None, "") else None,
                "balance": float(balance_raw) if balance_raw not in (None, "") else None,
                "drawdown_headroom": float(headroom_raw) if headroom_raw not in (None, "") else None,
                "daily_pnl": daily_pnl,
                "week_pnl": week_pnl,
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