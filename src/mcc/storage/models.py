"""SQLAlchemy models for durable relational state."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(String, primary_key=True)
    status = Column(String, default="DRAFT")


class AccountState(Base):
    __tablename__ = "account_states"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
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
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    symbol = Column(String, default="")
    decision = Column(String, default="NO_GO")
    reason = Column(Text, default="")
    vetoes = Column(Text, default="")


class ReportMetadata(Base):
    __tablename__ = "report_metadata"
    id = Column(String, primary_key=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    report_type = Column(String, default="pdf")
    object_key = Column(String, nullable=False)
    storage_backend = Column(String, default="local")
    size_bytes = Column(Integer, default=0)
    checksum = Column(String, default="")


class AgentHeartbeat(Base):
    __tablename__ = "agent_heartbeats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    service_mode = Column(String, default="worker")
    agent_count = Column(Integer, default=0)
    healthy_count = Column(Integer, default=0)
    kill_active = Column(Boolean, default=False)
    status = Column(String, default="ok")