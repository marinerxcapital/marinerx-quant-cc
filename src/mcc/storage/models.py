"""SQLAlchemy models for durable relational state."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String, default="")
    asset_class = Column(String, default="futures")
    exchange = Column(String, default="")
    tick_size = Column(Float, default=0.25)
    tick_value = Column(Float, default=5.0)
    point_value = Column(Float, default=20.0)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text, default="{}")
    source = Column(String, default="system")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class MarketBar(Base):
    __tablename__ = "market_bars"
    __table_args__ = (Index("ix_market_bars_sym_tf_ts", "symbol", "timeframe", "timestamp"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, default=0.0)
    high = Column(Float, default=0.0)
    low = Column(Float, default=0.0)
    close = Column(Float, default=0.0)
    volume = Column(Float, default=0.0)
    source = Column(String, default="demo")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    snapshot_json = Column(Text, default="{}")
    source = Column(String, default="system")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class MacroSeries(Base):
    __tablename__ = "macro_series"
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String, nullable=False, unique=True)
    name = Column(String, default="")
    source = Column(String, default="fred")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class MacroObservation(Base):
    __tablename__ = "macro_observations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String, nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    value = Column(Float, default=0.0)
    source = Column(String, default="fred")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class RegimeSnapshot(Base):
    __tablename__ = "regime_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, default="15m")
    volatility_regime = Column(String, default="NORMAL")
    trend_state = Column(String, default="RANGING")
    confidence = Column(Float, default=0.0)
    rationale = Column(Text, default="")
    snapshot_json = Column(Text, default="{}")
    source = Column(String, default="regime_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(String, primary_key=True)
    name = Column(String, default="")
    description = Column(Text, default="")
    instrument = Column(String, default="")
    timeframe = Column(String, default="")
    status = Column(String, default="DRAFT")
    version = Column(Integer, default=1)
    owner_agent = Column(String, default="ResearchLab")
    hypothesis = Column(Text, default="")
    entry_rules = Column(Text, default="")
    exit_rules = Column(Text, default="")
    risk_rules = Column(Text, default="")
    parameters_json = Column(Text, default="{}")
    tags = Column(String, default="")
    latest_verdict = Column(String, default="")
    latest_validation_id = Column(String, default="")
    archived_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, default="registry")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    @property
    def strategy_id(self) -> str:
        return self.id


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, nullable=False, index=True)
    version = Column(Integer, default=1)
    change_note = Column(Text, default="")
    parameters_json = Column(Text, default="{}")
    rules_snapshot_json = Column(Text, default="{}")
    created_by = Column(String, default="system")
    source = Column(String, default="registry")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, default="15m")
    start_date = Column(String, default="")
    end_date = Column(String, default="")
    initial_equity = Column(Float, default=100000.0)
    risk_per_trade = Column(Float, default=350.0)
    commission_per_contract = Column(Float, default=2.5)
    slippage_ticks = Column(Float, default=1.0)
    metrics_json = Column(Text, default="{}")
    equity_curve_json = Column(Text, default="[]")
    trade_list_json = Column(Text, default="[]")
    config_hash = Column(String, default="")
    source = Column(String, default="backtest_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ValidationResult(Base):
    __tablename__ = "validation_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, nullable=False, index=True)
    symbol = Column(String, default="")
    timeframe = Column(String, default="")
    date_range_json = Column(Text, default="{}")
    fold_count = Column(Integer, default=0)
    metrics_json = Column(Text, default="{}")
    walk_forward_folds_json = Column(Text, default="[]")
    monte_carlo_json = Column(Text, default="{}")
    verdict = Column(String, default="YELLOW")
    rationale = Column(Text, default="")
    source = Column(String, default="validation_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class TradeDecision(Base):
    __tablename__ = "trade_decisions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, default="")
    strategy_id = Column(String, default="")
    decision = Column(String, default="NO-GO")
    confidence = Column(Float, default=0.0)
    rationale = Column(Text, default="")
    vetoes_json = Column(Text, default="[]")
    factor_scores_json = Column(Text, default="{}")
    risk_snapshot_json = Column(Text, default="{}")
    data_freshness_snapshot_json = Column(Text, default="{}")
    strategy_verdict = Column(String, default="")
    regime_snapshot_json = Column(Text, default="{}")
    source = Column(String, default="decision_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False)
    side = Column(String, default="BUY")
    quantity = Column(Integer, default=1)
    order_type = Column(String, default="MARKET")
    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    fill_price = Column(Float, nullable=True)
    reason = Column(Text, default="")
    linked_decision_id = Column(Integer, nullable=True)
    risk_check_id = Column(Integer, nullable=True)
    source = Column(String, default="paper")
    metadata_json = Column(Text, default="{}")
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String, nullable=False, unique=True)
    date = Column(String, default="")
    symbol = Column(String, default="")
    strategy_id = Column(String, default="")
    decision_id = Column(Integer, nullable=True)
    order_id = Column(String, default="")
    setup = Column(Text, default="")
    execution_notes = Column(Text, default="")
    risk_notes = Column(Text, default="")
    mistakes = Column(Text, default="")
    screenshots_json = Column(Text, default="[]")
    tags = Column(String, default="")
    rating = Column(Integer, default=0)
    source = Column(String, default="journal")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class PerformanceDaily(Base):
    __tablename__ = "performance_daily"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, index=True)
    daily_pnl = Column(Float, default=0.0)
    cumulative_pnl = Column(Float, default=0.0)
    trade_count = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    metadata_json = Column(Text, default="{}")
    source = Column(String, default="performance")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, default="info")
    symbol = Column(String, default="")
    strategy_id = Column(String, default="")
    order_id = Column(String, default="")
    message = Column(Text, default="")
    risk_state_json = Column(Text, default="{}")
    source = Column(String, default="risk_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class RiskSettings(Base):
    __tablename__ = "risk_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_loss_limit = Column(Float, default=1500.0)
    weekly_loss_limit = Column(Float, default=3000.0)
    max_drawdown_limit = Column(Float, default=5000.0)
    risk_per_trade_pct = Column(Float, default=0.5)
    max_contracts_per_symbol = Column(Integer, default=4)
    max_open_positions = Column(Integer, default=3)
    lockout_after_loss_count = Column(Integer, default=3)
    live_execution_enabled = Column(Boolean, default=False)
    paper_trading_enabled = Column(Boolean, default=True)
    kill_switch_active = Column(Boolean, default=False)
    current_day_pnl = Column(Float, default=0.0)
    current_week_pnl = Column(Float, default=0.0)
    drawdown = Column(Float, default=0.0)
    source = Column(String, default="risk_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, nullable=False, unique=True)
    report_type = Column(String, default="DAILY_RESEARCH_BRIEF")
    title = Column(String, default="")
    format = Column(String, default="markdown")
    path = Column(String, default="")
    content_json = Column(Text, default="{}")
    source = Column(String, default="report_engine")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class SystemEvent(Base):
    __tablename__ = "system_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    component = Column(String, default="system")
    status = Column(String, default="ok")
    message = Column(Text, default="")
    source = Column(String, default="system")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class AccountState(Base):
    __tablename__ = "account_states"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=_utcnow)
    equity = Column(Float, default=0.0)
    cash = Column(Float, default=0.0)
    day_pnl = Column(Float, default=0.0)
    drawdown = Column(Float, default=0.0)
    source = Column(String, default="unknown")


class Trade(Base):
    __tablename__ = "trades"
    id = Column(String, primary_key=True)
    ts_utc = Column(DateTime(timezone=True))
    symbol = Column(String)
    side = Column(String)
    qty = Column(Integer)
    price = Column(Float)
    pnl = Column(Float, default=0.0)


class DecisionLog(Base):
    __tablename__ = "decision_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=_utcnow)
    symbol = Column(String, default="")
    decision = Column(String, default="NO_GO")
    reason = Column(Text, default="")
    vetoes = Column(Text, default="")


class ReportMetadata(Base):
    __tablename__ = "report_metadata"
    id = Column(String, primary_key=True)
    ts_utc = Column(DateTime(timezone=True), default=_utcnow)
    report_type = Column(String, default="pdf")
    object_key = Column(String, nullable=False)
    storage_backend = Column(String, default="local")
    size_bytes = Column(Integer, default=0)
    checksum = Column(String, default="")


class AgentHeartbeat(Base):
    __tablename__ = "agent_heartbeats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=_utcnow)
    service_mode = Column(String, default="worker")
    agent_count = Column(Integer, default=0)
    healthy_count = Column(Integer, default=0)
    kill_active = Column(Boolean, default=False)
    status = Column(String, default="ok")