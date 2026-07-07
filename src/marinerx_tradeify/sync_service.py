from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from marinerx_tradeify.connectors.normalizer import (
    data_health_gate_decision,
    merge_with_reconciliation,
)
from marinerx_tradeify.connectors.tradeify_dashboard_connector import (
    TradeifyDashboardConfig,
    TradeifyDashboardConnector,
    TradeifyDashboardError,
    TradeifySessionError,
)
from marinerx_tradeify.connectors.tradovate_connector import (
    TradovateConfig,
    TradovateConfigurationError,
    TradovateConnector,
    TradovateError,
)
from marinerx_tradeify.models import GateResult, SignalIntent, TradeDecision
from marinerx_tradeify.persistence import load_latest_snapshot, save_snapshot, save_sync_event
from marinerx_tradeify.risk_engine import gate_trade

_service: Optional["TradeifyDataSyncService"] = None


def _env_bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default).lower()).lower() in ("1", "true", "yes", "on")


class TradeifyDataSyncService:
    def __init__(self) -> None:
        self._memory_cache: dict[str, Any] | None = None

    @property
    def data_enabled(self) -> bool:
        return _env_bool("MARINERX_TRADEIFY_DATA_ENABLED", True)

    @property
    def tradovate_enabled(self) -> bool:
        return _env_bool("MARINERX_TRADOVATE_ENABLED", True)

    @property
    def dashboard_enabled(self) -> bool:
        return _env_bool("MARINERX_TRADEIFY_DASHBOARD_ENABLED", False)

    @property
    def live_orders_enabled(self) -> bool:
        return _env_bool("MARINERX_ALLOW_LIVE_ORDERS", False)

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": self.data_enabled,
            "tradovate_enabled": self.tradovate_enabled,
            "tradeify_dashboard_enabled": self.dashboard_enabled,
            "live_orders_enabled": self.live_orders_enabled,
            "mode": os.getenv("MARINERX_TRADEIFY_MODE", "PAPER_FIRST"),
            "status": "configured" if self.data_enabled else "disabled",
            "message": "Tradeify 150K data connectors active" if self.data_enabled else "Data sync disabled",
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_health(self) -> dict[str, Any]:
        tradovate_state = "not_configured"
        dashboard_state = "disabled"

        if self.tradovate_enabled:
            try:
                TradovateConfig.from_env().validate_credentials()
                tradovate_state = "configured"
            except TradovateConfigurationError:
                tradovate_state = "not_configured"

        if self.dashboard_enabled:
            dash = TradeifyDashboardConnector(TradeifyDashboardConfig.from_env())
            session = dash.validate_session()
            dashboard_state = "connected" if session.get("dashboard_session_valid") else session.get("status", "reconnect_required")
        elif not self.dashboard_enabled:
            dashboard_state = "disabled"

        latest = self.get_latest()
        stale_block = False
        if latest and latest.get("reconciliation", {}).get("block_trades"):
            stale_block = True

        return {
            "status": "healthy" if self.data_enabled and not stale_block else "degraded",
            "tradovate_connector": tradovate_state,
            "tradeify_dashboard_connector": dashboard_state,
            "safe_default": "BLOCK_NEW_TRADES",
            "live_orders_enabled": self.live_orders_enabled,
            "data_enabled": self.data_enabled,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_latest(self) -> dict[str, Any]:
        if self._memory_cache:
            return self._memory_cache
        cached = load_latest_snapshot()
        if cached:
            self._memory_cache = cached
            return cached
        return {
            "status": "not_available",
            "safe_default": "BLOCK_NEW_TRADES",
            "message": "No cached account snapshot. Run POST /api/tradeify/150k/data/sync after configuring connectors.",
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def sync(self) -> dict[str, Any]:
        if not self.data_enabled:
            save_sync_event("sync", "disabled", "MARINERX_TRADEIFY_DATA_ENABLED=false")
            return {
                "status": "disabled",
                "safe_default": "BLOCK_NEW_TRADES",
                "message": "Tradeify data sync disabled by configuration.",
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }

        broker = None
        dashboard = None
        errors: list[str] = []

        tradovate = TradovateConnector(TradovateConfig.from_env())
        try:
            if self.tradovate_enabled:
                accounts = await tradovate.fetch_accounts()
                acct = tradovate.select_account(accounts)
                broker = await tradovate.build_broker_metrics(
                    acct.get("id"),
                    account_name=str(acct.get("name", "Tradeify Tradovate")),
                )
        except TradovateConfigurationError as exc:
            errors.append(str(exc))
            save_sync_event("tradovate", "not_configured", str(exc))
        except TradovateError as exc:
            errors.append("Tradovate sync failed")
            save_sync_event("tradovate", "error", str(exc))
        finally:
            await tradovate.close()

        if broker is None:
            payload = self._block_payload(errors or ["Tradovate broker metrics unavailable"])
            self._memory_cache = payload
            save_snapshot(payload)
            return payload

        if self.dashboard_enabled:
            dash_conn = TradeifyDashboardConnector(TradeifyDashboardConfig.from_env())
            try:
                dashboard = await dash_conn.fetch_metrics()
            except (TradeifySessionError, TradeifyDashboardError) as exc:
                errors.append(str(exc))
                save_sync_event("tradeify_dashboard", "error", str(exc))

        snapshot, reconciliation = merge_with_reconciliation(
            broker,
            dashboard,
            dashboard_required=self.dashboard_enabled,
        )

        data_decision, data_reason = data_health_gate_decision(reconciliation)
        gate = gate_trade(
            snapshot,
            SignalIntent(
                symbol="MNQ",
                direction="LONG",
                setup_name="DATA_HEALTH_PROBE",
                entry_price=20000.0,
                stop_price=19950.0,
                target_price=20100.0,
                contract_type="micro",
                requested_contracts=1,
            ),
        )
        if data_decision == TradeDecision.BLOCK:
            gate = GateResult(
                decision=TradeDecision.BLOCK,
                approved_contracts=0,
                reason=data_reason,
                max_risk_dollars=gate.max_risk_dollars,
                projected_risk_dollars=0.0,
                drawdown_headroom_after_loss=snapshot.drawdown_headroom,
            )

        snap_dict = asdict(snapshot)
        snap_dict["drawdown_headroom"] = snapshot.drawdown_headroom
        snap_dict["phase"] = snapshot.phase.value

        payload: dict[str, Any] = {
            "status": "ok" if reconciliation.ok else "reconciliation_failed",
            "account_id_hash": broker.account_id_hash,
            "snapshot": snap_dict,
            "reconciliation": reconciliation.to_dict(),
            "gate_result": asdict(gate),
            "gate_result_decision": gate.decision.value,
            "errors": errors,
            "safe_default": "BLOCK_NEW_TRADES" if reconciliation.block_trades else "ALLOW_WITH_CAUTION",
            "live_orders_enabled": self.live_orders_enabled,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._memory_cache = payload
        save_snapshot(payload)
        save_sync_event("sync", payload["status"], "Sync completed", {"errors": errors})
        return payload

    def _block_payload(self, errors: list[str]) -> dict[str, Any]:
        return {
            "status": "error",
            "safe_default": "BLOCK_NEW_TRADES",
            "message": "; ".join(errors),
            "errors": errors,
            "reconciliation": {
                "ok": False,
                "block_trades": True,
                "status": "sync_failed",
                "reconciliation": "sync_failed",
                "warnings": errors,
            },
            "gate_result": {
                "decision": TradeDecision.BLOCK.value,
                "approved_contracts": 0,
                "reason": "DATA_SYNC_FAILED",
                "max_risk_dollars": 0.0,
                "projected_risk_dollars": 0.0,
                "drawdown_headroom_after_loss": 0.0,
            },
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    def reconcile_cached(self) -> dict[str, Any]:
        latest = self.get_latest()
        rec = latest.get("reconciliation")
        if rec:
            return rec
        return {
            "status": "unavailable",
            "reconciliation": "unavailable",
            "block_trades": True,
            "safe_default": "BLOCK_NEW_TRADES",
            "message": "No reconciliation data — sync required.",
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_dashboard_session(self) -> dict[str, Any]:
        if not self.dashboard_enabled:
            return {
                "dashboard_session_valid": False,
                "status": "disabled",
                "safe_default": "BLOCK_NEW_TRADES",
                "message": "Dashboard connector disabled (MARINERX_TRADEIFY_DASHBOARD_ENABLED=false).",
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }
        dash = TradeifyDashboardConnector(TradeifyDashboardConfig.from_env())
        result = dash.validate_session()
        result["safe_default"] = "BLOCK_NEW_TRADES" if not result.get("dashboard_session_valid") else "ALLOW_WITH_CAUTION"
        result["observed_at"] = datetime.now(timezone.utc).isoformat()
        return result


def get_sync_service() -> TradeifyDataSyncService:
    global _service
    if _service is None:
        _service = TradeifyDataSyncService()
    return _service