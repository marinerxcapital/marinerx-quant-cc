"""Test fixture-based scraping without live credentials."""

from __future__ import annotations

import pytest

from tradeify_sync.config import Settings
from tradeify_sync.normalize.mapper import to_account, to_trade
from tradeify_sync.scrapers.fixtures import scrape_accounts_fixture, scrape_trades_fixture


def test_scrape_accounts_fixture(settings: Settings) -> None:
    rows = scrape_accounts_fixture(settings)
    assert len(rows) == 2
    assert rows[0]["account_id"] == "ACC-001"
    assert rows[1]["account_id"] == "ACC-002"
    assert rows[0]["nickname"] == "Main Eval"
    assert rows[1]["phase"] == "FUNDED"


def test_scrape_trades_fixture(settings: Settings) -> None:
    rows = scrape_trades_fixture(settings, "ACC-001")
    assert len(rows) == 3
    assert rows[0]["trade_id"] == "T-1001"
    assert rows[0]["symbol_raw"] == "NQU25"
    assert rows[2]["side"] == "LONG"


def test_normalize_fixture_accounts(settings: Settings) -> None:
    rows = scrape_accounts_fixture(settings)
    acct = to_account(rows[0])
    assert acct.account_id == "ACC-001"
    assert acct.drawdown_headroom is not None
    assert acct.equity - acct.trailing_dd_floor == acct.drawdown_headroom


def test_normalize_fixture_trades(settings: Settings) -> None:
    rows = scrape_trades_fixture(settings)
    trade = to_trade(rows[0], "ACC-001", settings.sync.timezone_display)
    assert trade.symbol == "NQ"
    assert trade.qty == 2
    assert trade.source_hash
    assert len(trade.source_hash) == 64