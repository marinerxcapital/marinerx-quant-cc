"""Repository layer for research persistence."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from mcc.storage.models import (
    BacktestRun,
    Instrument,
    JournalEntry,
    MarketBar,
    Order,
    RegimeSnapshot,
    Report,
    RiskEvent,
    RiskSettings,
    Strategy,
    StrategyVersion,
    TradeDecision,
    ValidationResult,
)
from mcc.storage.session import session_scope

VALID_STRATEGY_STATUSES = {
    "DRAFT", "REGISTERED", "TESTED", "GREEN", "YELLOW", "RED", "ARCHIVED",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _json_loads(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default if default is not None else {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default if default is not None else {}


def strategy_to_dict(s: Strategy) -> dict[str, Any]:
    return {
        "strategy_id": s.id,
        "id": s.id,
        "name": s.name or "",
        "description": s.description or "",
        "instrument": s.instrument or "",
        "timeframe": s.timeframe or "",
        "status": s.status or "DRAFT",
        "version": s.version or 1,
        "owner_agent": s.owner_agent or "ResearchLab",
        "hypothesis": s.hypothesis or "",
        "entry_rules": s.entry_rules or "",
        "exit_rules": s.exit_rules or "",
        "risk_rules": s.risk_rules or "",
        "parameters_json": _json_loads(s.parameters_json, {}),
        "tags": (s.tags or "").split(",") if s.tags else [],
        "latest_verdict": s.latest_verdict or "",
        "latest_validation_id": s.latest_validation_id or "",
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "archived_at": s.archived_at.isoformat() if s.archived_at else None,
    }


class StrategyRepository:
    def list_strategies(
        self,
        *,
        status: str | None = None,
        instrument: str | None = None,
        timeframe: str | None = None,
        tag: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        with session_scope() as session:
            q = select(Strategy)
            rows = session.scalars(q).all()
            out = []
            for s in rows:
                if not include_archived and s.status == "ARCHIVED":
                    continue
                if status and s.status != status:
                    continue
                if instrument and s.instrument != instrument:
                    continue
                if timeframe and s.timeframe != timeframe:
                    continue
                if tag and tag not in (s.tags or ""):
                    continue
                out.append(strategy_to_dict(s))
            return out

    def get(self, strategy_id: str) -> dict[str, Any] | None:
        with session_scope() as session:
            s = session.get(Strategy, strategy_id)
            return strategy_to_dict(s) if s else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        sid = data.get("strategy_id") or data.get("id") or f"STR-{uuid.uuid4().hex[:8].upper()}"
        with session_scope() as session:
            s = Strategy(
                id=sid,
                name=data["name"],
                description=data.get("description", ""),
                instrument=data["instrument"],
                timeframe=data["timeframe"],
                status=data.get("status", "DRAFT"),
                version=data.get("version", 1),
                owner_agent=data.get("owner_agent", "ResearchLab"),
                hypothesis=data["hypothesis"],
                entry_rules=data["entry_rules"],
                exit_rules=data["exit_rules"],
                risk_rules=data["risk_rules"],
                parameters_json=_json_dumps(data.get("parameters_json", {})),
                tags=",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", ""),
                latest_verdict=data.get("latest_verdict", ""),
            )
            session.add(s)
            session.flush()
            return strategy_to_dict(s)

    def update(self, strategy_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        with session_scope() as session:
            s = session.get(Strategy, strategy_id)
            if not s:
                return None
            if "status" in data and data["status"] not in VALID_STRATEGY_STATUSES:
                raise ValueError(f"Invalid status: {data['status']}")
            for field in (
                "name", "description", "instrument", "timeframe", "status",
                "owner_agent", "hypothesis", "entry_rules", "exit_rules", "risk_rules",
                "latest_verdict", "latest_validation_id",
            ):
                if field in data:
                    setattr(s, field, data[field])
            if "parameters_json" in data:
                s.parameters_json = _json_dumps(data["parameters_json"])
            if "tags" in data:
                tags = data["tags"]
                s.tags = ",".join(tags) if isinstance(tags, list) else str(tags)
            s.updated_at = _now()
            if any(k in data for k in ("entry_rules", "exit_rules", "risk_rules", "parameters_json")):
                s.version = (s.version or 1) + 1
                session.add(StrategyVersion(
                    strategy_id=s.id,
                    version=s.version,
                    change_note=data.get("change_note", "rules or parameters updated"),
                    parameters_json=s.parameters_json or "{}",
                    rules_snapshot_json=_json_dumps({
                        "entry_rules": s.entry_rules,
                        "exit_rules": s.exit_rules,
                        "risk_rules": s.risk_rules,
                    }),
                ))
            session.flush()
            return strategy_to_dict(s)

    def archive(self, strategy_id: str) -> dict[str, Any] | None:
        with session_scope() as session:
            s = session.get(Strategy, strategy_id)
            if not s:
                return None
            s.status = "ARCHIVED"
            s.archived_at = _now()
            s.updated_at = _now()
            session.flush()
            return strategy_to_dict(s)


class BacktestRepository:
    def save_run(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = BacktestRun(
                strategy_id=data["strategy_id"],
                symbol=data["symbol"],
                timeframe=data.get("timeframe", "15m"),
                start_date=data.get("start_date", ""),
                end_date=data.get("end_date", ""),
                initial_equity=data.get("initial_equity", 100000.0),
                risk_per_trade=data.get("risk_per_trade", 350.0),
                commission_per_contract=data.get("commission_per_contract", 2.5),
                slippage_ticks=data.get("slippage_ticks", 1.0),
                metrics_json=_json_dumps(data.get("metrics", {})),
                equity_curve_json=_json_dumps(data.get("equity_curve", [])),
                trade_list_json=_json_dumps(data.get("trade_list", [])),
                config_hash=data.get("config_hash", ""),
            )
            session.add(row)
            session.flush()
            return {"id": row.id, **data, "created_at": row.created_at.isoformat() if row.created_at else None}

    def get(self, run_id: int) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.get(BacktestRun, run_id)
            if not row:
                return None
            return {
                "id": row.id,
                "strategy_id": row.strategy_id,
                "symbol": row.symbol,
                "metrics": _json_loads(row.metrics_json),
                "equity_curve": _json_loads(row.equity_curve_json, []),
                "trade_list": _json_loads(row.trade_list_json, []),
                "config_hash": row.config_hash,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }


class DecisionRepository:
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = TradeDecision(
                symbol=data.get("symbol", ""),
                strategy_id=data.get("strategy_id", ""),
                decision=data.get("decision", "NO-GO"),
                confidence=data.get("confidence", 0.0),
                rationale=data.get("rationale", ""),
                vetoes_json=_json_dumps(data.get("vetoes", [])),
                factor_scores_json=_json_dumps(data.get("factor_scores", {})),
                risk_snapshot_json=_json_dumps(data.get("risk_snapshot", {})),
                data_freshness_snapshot_json=_json_dumps(data.get("data_freshness_snapshot", {})),
                strategy_verdict=data.get("strategy_verdict", ""),
                regime_snapshot_json=_json_dumps(data.get("regime_snapshot", {})),
            )
            session.add(row)
            session.flush()
            return {**data, "decision_id": row.id, "created_at": row.created_at.isoformat() if row.created_at else None}

    def get_latest(self, symbol: str | None = None) -> dict[str, Any] | None:
        with session_scope() as session:
            q = select(TradeDecision).order_by(desc(TradeDecision.created_at))
            if symbol:
                q = q.where(TradeDecision.symbol == symbol)
            row = session.scalars(q).first()
            if not row:
                return None
            return {
                "decision_id": row.id,
                "symbol": row.symbol,
                "strategy_id": row.strategy_id,
                "decision": row.decision,
                "confidence": row.confidence,
                "rationale": row.rationale,
                "vetoes": _json_loads(row.vetoes_json, []),
                "factor_scores": _json_loads(row.factor_scores_json, {}),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }


class RiskRepository:
    def get_or_create_settings(self, session: Session) -> RiskSettings:
        row = session.scalars(select(RiskSettings).limit(1)).first()
        if row:
            return row
        row = RiskSettings()
        session.add(row)
        session.flush()
        return row

    def get_settings(self) -> dict[str, Any]:
        with session_scope() as session:
            row = self.get_or_create_settings(session)
            return self._settings_dict(row)

    def update_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = self.get_or_create_settings(session)
            for field in (
                "daily_loss_limit", "weekly_loss_limit", "max_drawdown_limit",
                "risk_per_trade_pct", "max_contracts_per_symbol", "max_open_positions",
                "lockout_after_loss_count", "live_execution_enabled", "paper_trading_enabled",
                "current_day_pnl", "current_week_pnl", "drawdown",
            ):
                if field in data:
                    setattr(row, field, data[field])
            row.updated_at = _now()
            session.flush()
            return self._settings_dict(row)

    def set_kill_switch(self, active: bool) -> dict[str, Any]:
        with session_scope() as session:
            row = self.get_or_create_settings(session)
            row.kill_switch_active = active
            row.updated_at = _now()
            event_type = "KILL_SWITCH_ACTIVATED" if active else "KILL_SWITCH_CLEARED"
            session.add(RiskEvent(
                event_type=event_type,
                severity="critical" if active else "info",
                message=f"Kill switch {'activated' if active else 'cleared'}",
                risk_state_json=_json_dumps(self._settings_dict(row)),
            ))
            session.flush()
            return self._settings_dict(row)

    def record_event(self, event_type: str, message: str, **kwargs: Any) -> int:
        with session_scope() as session:
            ev = RiskEvent(
                event_type=event_type,
                severity=kwargs.get("severity", "warning"),
                symbol=kwargs.get("symbol", ""),
                strategy_id=kwargs.get("strategy_id", ""),
                order_id=kwargs.get("order_id", ""),
                message=message,
                risk_state_json=_json_dumps(kwargs.get("risk_state", {})),
            )
            session.add(ev)
            session.flush()
            return ev.id

    @staticmethod
    def _settings_dict(row: RiskSettings) -> dict[str, Any]:
        daily_remaining = max(0.0, row.daily_loss_limit + row.current_day_pnl)
        dd_headroom = max(0.0, row.max_drawdown_limit - abs(row.drawdown))
        return {
            "daily_loss_limit": row.daily_loss_limit,
            "weekly_loss_limit": row.weekly_loss_limit,
            "max_drawdown_limit": row.max_drawdown_limit,
            "risk_per_trade_pct": row.risk_per_trade_pct,
            "max_contracts_per_symbol": row.max_contracts_per_symbol,
            "max_open_positions": row.max_open_positions,
            "lockout_after_loss_count": row.lockout_after_loss_count,
            "live_execution_enabled": row.live_execution_enabled,
            "paper_trading_enabled": row.paper_trading_enabled,
            "kill_switch_active": row.kill_switch_active,
            "current_day_pnl": row.current_day_pnl,
            "current_week_pnl": row.current_week_pnl,
            "drawdown": row.drawdown,
            "drawdown_headroom": dd_headroom,
            "daily_loss_remaining": daily_remaining,
            "is_locked": row.kill_switch_active or row.current_day_pnl <= -row.daily_loss_limit,
            "last_updated": row.updated_at.isoformat() if row.updated_at else None,
        }


class InstrumentRepository:
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = Instrument(**{k: v for k, v in data.items() if hasattr(Instrument, k)})
            session.add(row)
            session.flush()
            return {"id": row.id, "symbol": row.symbol, "name": row.name}

    def list_active(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(select(Instrument).where(Instrument.is_active == True)).all()  # noqa: E712
            return [{"id": r.id, "symbol": r.symbol, "name": r.name, "asset_class": r.asset_class} for r in rows]


class MarketBarRepository:
    def save_bars(self, bars: list[dict[str, Any]]) -> int:
        with session_scope() as session:
            count = 0
            for b in bars:
                session.add(MarketBar(
                    symbol=b["symbol"],
                    timeframe=b.get("timeframe", "15m"),
                    timestamp=b["timestamp"],
                    open=b.get("open", 0),
                    high=b.get("high", 0),
                    low=b.get("low", 0),
                    close=b.get("close", 0),
                    volume=b.get("volume", 0),
                    source=b.get("source", "demo"),
                ))
                count += 1
            return count

    def get_bars(self, symbol: str, timeframe: str, limit: int = 500) -> list[dict[str, Any]]:
        with session_scope() as session:
            q = (
                select(MarketBar)
                .where(MarketBar.symbol == symbol, MarketBar.timeframe == timeframe)
                .order_by(desc(MarketBar.timestamp))
                .limit(limit)
            )
            rows = session.scalars(q).all()
            return [
                {
                    "symbol": r.symbol,
                    "timeframe": r.timeframe,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "open": r.open, "high": r.high, "low": r.low, "close": r.close,
                    "volume": r.volume, "source": r.source,
                }
                for r in reversed(rows)
            ]


class JournalRepository:
    def list_entries(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(select(JournalEntry).order_by(desc(JournalEntry.created_at))).all()
            return [self._to_dict(r) for r in rows]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        eid = data.get("entry_id") or f"JNL-{uuid.uuid4().hex[:8].upper()}"
        with session_scope() as session:
            row = JournalEntry(
                entry_id=eid,
                date=data.get("date", ""),
                symbol=data.get("symbol", ""),
                strategy_id=data.get("strategy_id", ""),
                decision_id=data.get("decision_id"),
                order_id=data.get("order_id", ""),
                setup=data.get("setup", ""),
                execution_notes=data.get("execution_notes", ""),
                risk_notes=data.get("risk_notes", ""),
                mistakes=data.get("mistakes", ""),
                screenshots_json=_json_dumps(data.get("screenshots", [])),
                tags=data.get("tags", ""),
                rating=data.get("rating", 0),
            )
            session.add(row)
            session.flush()
            return self._to_dict(row)

    def update(self, entry_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.scalars(select(JournalEntry).where(JournalEntry.entry_id == entry_id)).first()
            if not row:
                return None
            for field in ("date", "symbol", "strategy_id", "setup", "execution_notes", "risk_notes", "mistakes", "tags", "rating"):
                if field in data:
                    setattr(row, field, data[field])
            if "screenshots" in data:
                row.screenshots_json = _json_dumps(data["screenshots"])
            row.updated_at = _now()
            session.flush()
            return self._to_dict(row)

    def delete(self, entry_id: str) -> bool:
        with session_scope() as session:
            row = session.scalars(select(JournalEntry).where(JournalEntry.entry_id == entry_id)).first()
            if not row:
                return False
            session.delete(row)
            return True

    @staticmethod
    def _to_dict(row: JournalEntry) -> dict[str, Any]:
        return {
            "id": row.id,
            "entry_id": row.entry_id,
            "date": row.date,
            "symbol": row.symbol,
            "strategy_id": row.strategy_id,
            "decision_id": row.decision_id,
            "order_id": row.order_id,
            "setup": row.setup,
            "execution_notes": row.execution_notes,
            "risk_notes": row.risk_notes,
            "mistakes": row.mistakes,
            "screenshots": _json_loads(row.screenshots_json, []),
            "tags": row.tags,
            "rating": row.rating,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class OrderRepository:
    def list_orders(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(select(Order).order_by(desc(Order.created_at))).all()
            return [self._to_dict(r) for r in rows]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        oid = data.get("order_id") or f"PPR-{uuid.uuid4().hex[:8].upper()}"
        with session_scope() as session:
            row = Order(
                order_id=oid,
                symbol=data["symbol"],
                side=data.get("side", "BUY"),
                quantity=data.get("quantity", 1),
                order_type=data.get("order_type", "MARKET"),
                limit_price=data.get("limit_price"),
                stop_price=data.get("stop_price"),
                status=data.get("status", "PENDING"),
                reason=data.get("reason", ""),
                linked_decision_id=data.get("linked_decision_id"),
                risk_check_id=data.get("risk_check_id"),
            )
            session.add(row)
            session.flush()
            return self._to_dict(row)

    def cancel(self, order_id: str) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.scalars(select(Order).where(Order.order_id == order_id)).first()
            if not row:
                return None
            row.status = "CANCELLED"
            row.updated_at = _now()
            session.flush()
            return self._to_dict(row)

    @staticmethod
    def _to_dict(row: Order) -> dict[str, Any]:
        return {
            "id": row.id,
            "order_id": row.order_id,
            "symbol": row.symbol,
            "side": row.side,
            "quantity": row.quantity,
            "order_type": row.order_type,
            "status": row.status,
            "fill_price": row.fill_price,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class ValidationRepository:
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = ValidationResult(
                strategy_id=data["strategy_id"],
                symbol=data.get("symbol", ""),
                timeframe=data.get("timeframe", ""),
                date_range_json=_json_dumps(data.get("date_range", {})),
                fold_count=data.get("fold_count", 0),
                metrics_json=_json_dumps(data.get("metrics", {})),
                walk_forward_folds_json=_json_dumps(data.get("walk_forward_folds", [])),
                monte_carlo_json=_json_dumps(data.get("monte_carlo", {})),
                verdict=data.get("verdict", "YELLOW"),
                rationale=data.get("rationale", ""),
            )
            session.add(row)
            session.flush()
            return {"id": row.id, **data}


class RegimeRepository:
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = RegimeSnapshot(
                symbol=data["symbol"],
                timeframe=data.get("timeframe", "15m"),
                volatility_regime=data.get("volatility_regime", "NORMAL"),
                trend_state=data.get("trend_state", "RANGING"),
                confidence=data.get("confidence", 0.0),
                rationale=data.get("rationale", ""),
                snapshot_json=_json_dumps(data),
            )
            session.add(row)
            session.flush()
            return {"id": row.id, **data, "last_updated": row.created_at.isoformat() if row.created_at else None}

    def get_latest(self, symbol: str) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.scalars(
                select(RegimeSnapshot).where(RegimeSnapshot.symbol == symbol).order_by(desc(RegimeSnapshot.created_at))
            ).first()
            if not row:
                return None
            return {
                "symbol": row.symbol,
                "timeframe": row.timeframe,
                "volatility_regime": row.volatility_regime,
                "trend_state": row.trend_state,
                "confidence": row.confidence,
                "rationale": row.rationale,
                "last_updated": row.created_at.isoformat() if row.created_at else None,
            }


class ReportRepository:
    def list_reports(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(select(Report).order_by(desc(Report.created_at))).all()
            return [{"id": r.id, "report_id": r.report_id, "report_type": r.report_type, "title": r.title, "format": r.format, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        rid = data.get("report_id") or f"RPT-{uuid.uuid4().hex[:8].upper()}"
        with session_scope() as session:
            row = Report(
                report_id=rid,
                report_type=data.get("report_type", "DAILY_RESEARCH_BRIEF"),
                title=data.get("title", ""),
                format=data.get("format", "markdown"),
                path=data.get("path", ""),
                content_json=_json_dumps(data.get("content", {})),
            )
            session.add(row)
            session.flush()
            return {"id": row.id, "report_id": rid, **data}

    def get(self, report_id: str) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.scalars(select(Report).where(Report.report_id == report_id)).first()
            if not row:
                return None
            return {
                "report_id": row.report_id,
                "report_type": row.report_type,
                "title": row.title,
                "format": row.format,
                "path": row.path,
                "content": _json_loads(row.content_json),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }