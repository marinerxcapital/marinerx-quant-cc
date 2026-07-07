"""Raw dict to Pydantic model mapping."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from tradeify_sync.constants import IntegrityError
from tradeify_sync.models import Account, Phase, PayoutRecord, Side, Trade
from tradeify_sync.utils.timeparse import parse_dashboard_timestamp, to_utc


def money(raw: str | None) -> Decimal | None:
    """Parse a money string to Decimal."""
    if raw is None or str(raw).strip() == "":
        return None
    text = str(raw).strip().replace("$", "").replace(",", "")
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    try:
        val = Decimal(text)
        return -val if negative else val
    except InvalidOperation as exc:
        raise IntegrityError(f"Unparseable money value: {raw}") from exc


def qty(raw: str | None) -> int:
    """Parse quantity string to int."""
    if raw is None or str(raw).strip() == "":
        raise IntegrityError("Missing quantity")
    text = str(raw).strip().replace(",", "")
    try:
        return int(float(text))
    except ValueError as exc:
        raise IntegrityError(f"Unparseable qty: {raw}") from exc


def _parse_side(raw: str) -> Side:
    val = raw.strip().upper()
    if val in ("LONG", "L", "BUY"):
        return Side.LONG
    if val in ("SHORT", "S", "SELL"):
        return Side.SHORT
    raise IntegrityError(f"Unparseable side: {raw}")


def _parse_phase(raw: str) -> Phase:
    val = raw.strip().upper()
    try:
        return Phase(val)
    except ValueError:
        return Phase.EVAL


def _parse_bool(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in ("true", "yes", "1", "eligible")


def root_from_symbol(raw: str) -> str:
    """Strip contract month/year to instrument root."""
    text = raw.strip().upper()
    known_roots = ("MNQ", "MES", "MCL", "MGC", "NQ", "ES", "CL", "GC")
    for root in sorted(known_roots, key=len, reverse=True):
        if text.startswith(root):
            return root
    match = re.match(r"^([A-Z]{1,3})[FGHJKMNQUVXZ]\d+$", text)
    if match:
        return match.group(1)
    match = re.match(r"^([A-Z]{1,3})", text)
    return match.group(1) if match else text


def to_account(raw: dict[str, str], now_utc: datetime | None = None) -> Account:
    """Map raw account dict to Account model."""
    ts = now_utc or datetime.now(UTC)
    return Account(
        account_id=raw.get("account_id", "").strip(),
        nickname=raw.get("nickname", ""),
        program=raw.get("program", ""),
        phase=_parse_phase(raw.get("phase", "EVAL")),
        size_usd=money(raw.get("size_usd")),
        platform=raw.get("platform", ""),
        status=raw.get("status", ""),
        balance=money(raw.get("balance")),
        equity=money(raw.get("equity")),
        high_water_mark=money(raw.get("high_water_mark")),
        trailing_dd_amount=money(raw.get("trailing_dd_amount")),
        trailing_dd_floor=money(raw.get("trailing_dd_floor")),
        daily_loss_limit=money(raw.get("daily_loss_limit")),
        daily_pnl=money(raw.get("daily_pnl")),
        days_traded=int(raw["days_traded"]) if raw.get("days_traded") else None,
        consistency_metric=money(raw.get("consistency_metric")),
        payout_eligible=_parse_bool(raw.get("payout_eligible")),
        last_synced_utc=ts,
    )


def to_trade(raw: dict[str, str], account_id: str, display_tz: str) -> Trade:
    """Map raw trade dict to Trade model."""
    symbol_raw = raw.get("symbol_raw", raw.get("symbol", "")).strip()
    return Trade(
        trade_id=raw.get("trade_id", ""),
        account_id=account_id,
        symbol_raw=symbol_raw,
        symbol=root_from_symbol(symbol_raw),
        side=_parse_side(raw.get("side", "LONG")),
        qty=qty(raw.get("qty")),
        entry_time_utc=parse_dashboard_timestamp(raw["entry_time"], display_tz),
        entry_price=money(raw["entry_price"]) or Decimal("0"),
        exit_time_utc=parse_dashboard_timestamp(raw["exit_time"], display_tz),
        exit_price=money(raw["exit_price"]) or Decimal("0"),
        gross_pnl=money(raw.get("gross_pnl")),
        fees=money(raw.get("fees")),
        net_pnl=money(raw.get("net_pnl")),
    )


def to_payout(raw: dict[str, str], account_id: str, display_tz: str) -> PayoutRecord:
    """Map raw payout dict to PayoutRecord."""
    processed = raw.get("processed_date")
    return PayoutRecord(
        account_id=account_id,
        request_date_utc=parse_dashboard_timestamp(raw["request_date"], display_tz),
        amount=money(raw["amount"]) or Decimal("0"),
        status=raw.get("status", ""),
        processed_date_utc=parse_dashboard_timestamp(processed, display_tz) if processed else None,
    )