"""System state and data freshness — honest NOMINAL/STALE/DEGRADED/LOCKED logic."""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Literal

from mcc.core.config import MCCSettings, get_settings
from mcc.data.live import free_market
from mcc.storage.database import check_database_connectivity
from mcc.storage.object_store import get_object_store

SystemStatusLabel = Literal["NOMINAL", "STALE", "DEGRADED", "LOCKED"]

MARKET_MAX_AGE_SEC = 180
ACCOUNT_MAX_AGE_SEC = 300
MACRO_MAX_AGE_SEC = 86400
RESEARCH_MAX_AGE_SEC = 86400


def _resolve_git_sha() -> str | None:
    for key in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "COMMIT_SHA"):
        val = os.environ.get(key)
        if val:
            return val[:40]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _get_supervisor() -> Any:
    from mcc.interface.web import server

    sup = server._SUP
    if sup is None:
        from mcc.runtime.bootstrap import create_supervisor

        sup = create_supervisor(replay=True)
    return sup


def _account_freshness() -> dict[str, Any]:
    try:
        from marinerx_tradeify.sync_service import get_sync_service

        svc = get_sync_service()
        health = svc.get_health()
        latest = svc.get_latest()
        observed = latest.get("observed_at") if latest else None
        age: int | None = None
        if observed:
            try:
                ts = datetime.fromisoformat(str(observed).replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age = max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
            except (TypeError, ValueError):
                age = None
        tradovate = health.get("tradovate", "not_configured")
        status = "missing"
        if age is not None:
            status = "fresh" if age <= ACCOUNT_MAX_AGE_SEC else "stale"
        elif tradovate == "not_configured":
            status = "not_configured"
        return {
            "source": "tradeify_tradovate",
            "last_updated": observed,
            "age_seconds": age,
            "max_age_seconds": ACCOUNT_MAX_AGE_SEC,
            "status": status,
            "tradovate_state": tradovate,
            "dashboard_state": health.get("tradeify_dashboard", "disabled"),
        }
    except Exception as exc:
        return {
            "source": "tradeify_tradovate",
            "last_updated": None,
            "age_seconds": None,
            "max_age_seconds": ACCOUNT_MAX_AGE_SEC,
            "status": "error",
            "error": str(exc),
        }


def _macro_freshness() -> dict[str, Any]:
    key = os.environ.get("FRED_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
    return {
        "source": "macro_provider",
        "last_updated": None,
        "age_seconds": None,
        "max_age_seconds": MACRO_MAX_AGE_SEC,
        "status": "not_configured" if not key else "missing",
        "api_key_present": bool(key),
    }


def _research_freshness() -> dict[str, Any]:
    return {
        "source": "research_pipeline",
        "last_updated": None,
        "age_seconds": None,
        "max_age_seconds": RESEARCH_MAX_AGE_SEC,
        "status": "missing",
    }


def _market_freshness() -> dict[str, Any]:
    cache = free_market.get_cache_freshness()
    keys = cache.get("cache_keys", {})
    ages = [v.get("age_seconds") for v in keys.values() if v.get("age_seconds") is not None]
    last_updates = [v.get("last_updated") for v in keys.values() if v.get("last_updated")]
    if not ages:
        return {
            "source": "yfinance_proxy",
            "last_updated": None,
            "age_seconds": None,
            "max_age_seconds": MARKET_MAX_AGE_SEC,
            "status": "missing",
        }
    max_age = max(ages)
    status = "fresh" if max_age <= MARKET_MAX_AGE_SEC else "stale"
    return {
        "source": "yfinance_proxy",
        "last_updated": max(last_updates) if last_updates else None,
        "age_seconds": max_age,
        "max_age_seconds": MARKET_MAX_AGE_SEC,
        "status": status,
        "cache_detail": keys,
    }


def build_data_freshness() -> dict[str, Any]:
    sources = {
        "market_data": _market_freshness(),
        "macro_data": _macro_freshness(),
        "account_sync": _account_freshness(),
        "research_runs": _research_freshness(),
    }
    critical_stale = any(
        sources[k]["status"] in ("stale", "missing")
        for k in ("market_data", "account_sync")
        if sources[k].get("status") != "not_configured"
    )
    any_stale = any(s["status"] == "stale" for s in sources.values())
    return {
        "sources": sources,
        "any_stale": any_stale,
        "critical_stale": critical_stale,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def _derive_status_label(
    kill_active: bool,
    risk_lockout: bool,
    freshness: dict[str, Any],
    db_ok: bool,
) -> SystemStatusLabel:
    if kill_active or risk_lockout:
        return "LOCKED"
    if freshness.get("critical_stale") or not db_ok:
        return "STALE"
    optional_missing = freshness["sources"]["macro_data"]["status"] in (
        "missing",
        "not_configured",
    )
    if optional_missing or freshness.get("any_stale"):
        return "DEGRADED"
    market = freshness["sources"]["market_data"]["status"]
    if market == "fresh":
        return "NOMINAL"
    return "DEGRADED"


def build_config_check(settings: MCCSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    checks: list[dict[str, str]] = []

    def add(name: str, present: bool, level: str) -> None:
        checks.append({"name": name, "presence": "PRESENT" if present else "MISSING", "level": level})

    add("DATABASE_URL", bool(settings.database_url), "REQUIRED" if settings.is_production else "OPTIONAL")
    add("ENABLE_LIVE_EXECUTION", settings.enable_live_execution, "OPTIONAL")
    add("R2_ACCOUNT_ID", bool(settings.r2_account_id), "REQUIRED" if settings.object_storage_backend == "r2" else "OPTIONAL")
    add("R2_ACCESS_KEY_ID", bool(settings.r2_access_key_id), "REQUIRED" if settings.object_storage_backend == "r2" else "OPTIONAL")
    add("R2_SECRET_ACCESS_KEY", bool(settings.r2_secret_access_key), "REQUIRED" if settings.object_storage_backend == "r2" else "OPTIONAL")
    add("R2_BUCKET_NAME", bool(settings.r2_bucket_name), "REQUIRED" if settings.object_storage_backend == "r2" else "OPTIONAL")
    add("TRADOVATE_CID", bool(os.environ.get("TRADOVATE_CID")), "OPTIONAL")
    add("TRADOVATE_SECRET", bool(os.environ.get("TRADOVATE_SECRET")), "OPTIONAL")
    add("TRADOVATE_USERNAME", bool(os.environ.get("TRADOVATE_USERNAME")), "OPTIONAL")
    add("TRADOVATE_PASSWORD", bool(os.environ.get("TRADOVATE_PASSWORD")), "OPTIONAL")
    add("FRED_API_KEY", bool(os.environ.get("FRED_API_KEY")), "OPTIONAL")
    add("ALPHA_VANTAGE_API_KEY", bool(os.environ.get("ALPHA_VANTAGE_API_KEY")), "OPTIONAL")

    required_missing = [c["name"] for c in checks if c["level"] == "REQUIRED" and c["presence"] == "MISSING"]
    return {
        "service": "MarinerX Labs Research System",
        "environment": settings.app_env,
        "checks": checks,
        "required_missing": required_missing,
        "ok": len(required_missing) == 0,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def build_version_info(settings: MCCSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    return {
        "service": "MarinerX Labs Research System",
        "version": settings.app_version,
        "git_sha": _resolve_git_sha(),
        "environment": settings.app_env,
        "service_mode": settings.service_mode,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def build_system_state(settings: MCCSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    sup = _get_supervisor()
    snap = sup.snapshot()
    freshness = build_data_freshness()
    db_health = check_database_connectivity()
    db_ok = db_health.get("status") == "ok"

    storage_health: dict[str, Any]
    try:
        storage_health = get_object_store(settings).health()
    except Exception as exc:
        storage_health = {"status": "error", "error": str(exc)}

    kill_active = bool(getattr(snap, "kill_active", False))
    risk_lockout = False
    try:
        from marinerx_tradeify.sync_service import get_sync_service

        latest = get_sync_service().get_latest()
        if latest and latest.get("block_trades"):
            risk_lockout = True
    except Exception:
        pass

    status_label = _derive_status_label(kill_active, risk_lockout, freshness, db_ok)

    agents_summary: dict[str, Any] = {}
    working = idle = error = 0
    for name, info in snap.agents.items():
        st = info.get("status", "unknown")
        agents_summary[name] = {"status": st, "task": info.get("task")}
        if st == "working":
            working += 1
        elif st == "error":
            error += 1
        else:
            idle += 1

    account = freshness["sources"]["account_sync"]
    header_pnl = {
        "day_pnl": None,
        "week_pnl": None,
        "drawdown_headroom": None,
        "source": "awaiting_sync",
        "labeled": True,
    }

    return {
        "status": status_label,
        "status_detail": {
            "database": db_health.get("status"),
            "object_storage": storage_health.get("status"),
            "kill_switch_active": kill_active,
            "risk_lockout": risk_lockout,
            "live_execution_enabled": settings.enable_live_execution,
            "paper_trading_enabled": not settings.enable_live_execution,
        },
        "version": settings.app_version,
        "git_sha": _resolve_git_sha(),
        "environment": settings.app_env,
        "service_mode": settings.service_mode,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agents": {
            "count": len(agents_summary),
            "working": working,
            "idle": idle,
            "error": error,
            "detail": agents_summary,
        },
        "header_metrics": header_pnl,
        "data_freshness_summary": {
            "any_stale": freshness.get("any_stale"),
            "critical_stale": freshness.get("critical_stale"),
            "market_data_status": freshness["sources"]["market_data"]["status"],
            "account_sync_status": account["status"],
        },
        "message": _status_message(status_label, freshness, kill_active),
    }


def _status_message(
    label: SystemStatusLabel,
    freshness: dict[str, Any],
    kill_active: bool,
) -> str:
    if kill_active:
        return "Kill switch active — new trades blocked."
    if label == "STALE":
        return "Critical data sources stale or missing — do not trade."
    if label == "DEGRADED":
        return "System operational with degraded or optional data gaps."
    if label == "NOMINAL":
        return "Required data sources fresh; no active lockouts."
    return "System state unknown."