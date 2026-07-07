"""Parse Tradeify TFD dashboard (app-f.tradeify.co) from visible page text."""
from __future__ import annotations

import re


def _money(raw: str) -> str:
    return raw.replace(",", "").strip()


def parse_accounts_from_text(text: str) -> list[dict[str, str]]:
    """Extract account rows from dashboard body text (SPA-rendered)."""
    if not text or "Account Balance" not in text:
        return []

    rows: list[dict[str, str]] = []
    # Split on account id markers (TDFY...)
    chunks = re.split(r"(?=TDFY[A-Z0-9]+\s*•?\s*Tradovate)", text)
    for chunk in chunks:
        acct_m = re.search(r"(TDFY[A-Z0-9]+)", chunk)
        if not acct_m:
            continue
        account_id = acct_m.group(1)

        program_m = re.search(
            r"(Select\s*\d+k|Growth\s*\d+k|Lightning\s*\d+k|\d+k\s*Select)",
            chunk,
            re.I,
        )
        balance_m = re.search(r"Account Balance\s*\$?([\d,]+\.?\d*)", chunk)
        dd_m = re.search(r"Trailing Max Drawdown\s*\$?([\d,]+\.?\d*)", chunk)
        daily_m = re.search(r"Daily P&?L\s*\$?([\d,]+\.?\d*)", chunk)
        status_m = re.search(r"\b(Active|Failed|Passed|Funded|Inactive)\b", chunk)

        program = program_m.group(1) if program_m else ""
        size_m = re.search(r"(\d+)", program)
        size_usd = size_m.group(1) + "000" if size_m else ""

        phase = "EVAL"
        upper = chunk.upper()
        if "FUNDED" in upper:
            phase = "FUNDED"
        elif "PASSED" in upper:
            phase = "PASSED"

        rows.append(
            {
                "account_id": account_id,
                "nickname": program or account_id,
                "program": program,
                "phase": phase,
                "size_usd": size_usd,
                "platform": "Tradovate",
                "status": status_m.group(1) if status_m else "Active",
                "balance": _money(balance_m.group(1)) if balance_m else "",
                "equity": _money(balance_m.group(1)) if balance_m else "",
                "trailing_dd_floor": _money(dd_m.group(1)) if dd_m else "",
                "daily_pnl": _money(daily_m.group(1)) if daily_m else "",
            }
        )

    if rows:
        return rows

    # Single-account fallback: whole page is one card
    acct_m = re.search(r"(TDFY[A-Z0-9]+)", text)
    if not acct_m:
        return []
    balance_m = re.search(r"Account Balance\s*\$?([\d,]+\.?\d*)", text)
    dd_m = re.search(r"Trailing Max Drawdown\s*\$?([\d,]+\.?\d*)", text)
    program_m = re.search(r"(Select\s*\d+k)", text, re.I)
    return [
        {
            "account_id": acct_m.group(1),
            "nickname": program_m.group(1) if program_m else acct_m.group(1),
            "program": program_m.group(1) if program_m else "",
            "phase": "EVAL",
            "size_usd": "150000",
            "platform": "Tradovate",
            "status": "Active",
            "balance": _money(balance_m.group(1)) if balance_m else "",
            "equity": _money(balance_m.group(1)) if balance_m else "",
            "trailing_dd_floor": _money(dd_m.group(1)) if dd_m else "",
            "daily_pnl": "",
        }
    ]