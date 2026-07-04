"""Minimal DB init for doctor gate. Extended for Phase 02 account sync tables."""
from __future__ import annotations
from typing import Any
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

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


def init_db(url: str = "sqlite:///:memory:") -> Any:
    eng = create_engine(
        url,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    Base.metadata.create_all(eng)
    return eng
