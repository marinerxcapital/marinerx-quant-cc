"""Fixture-based scraping for CI and offline tests."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from tradeify_sync.config import Settings, load_selectors


class _DataRowParser(HTMLParser):
    """Minimal HTML parser for data-attribute rows."""

    def __init__(self, row_attr: str, row_value: str | None = None) -> None:
        super().__init__()
        self.row_attr = row_attr
        self.row_value = row_value
        self.rows: list[dict[str, str]] = []
        self._in_row = False
        self._current: dict[str, str] = {}
        self._capture_tag: str | None = None
        self._capture_attr: str | None = None
        self._text_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v for k, v in attrs if v is not None}
        testid = attr_dict.get("data-testid", "")
        if self.row_attr == "data-testid" and testid == self.row_value:
            self._in_row = True
            self._current = {}
        elif self.row_attr in attr_dict and (self.row_value is None or attr_dict[self.row_attr] == self.row_value):
            self._in_row = True
            self._current = {}

        if self._in_row:
            _ALIASES = {
                "data-account-id": "account_id",
                "data-trade-id": "trade_id",
                "data-symbol": "symbol_raw",
                "data-dd-floor": "trailing_dd_floor",
                "data-trailing-dd": "trailing_dd_amount",
                "data-daily-loss-limit": "daily_loss_limit",
                "data-days-traded": "days_traded",
                "data-payout-eligible": "payout_eligible",
                "data-hwm": "high_water_mark",
                "data-entry-time": "entry_time",
                "data-exit-time": "exit_time",
                "data-entry-price": "entry_price",
                "data-exit-price": "exit_price",
                "data-gross-pnl": "gross_pnl",
                "data-net-pnl": "net_pnl",
            }
            for key, val in attr_dict.items():
                if key.startswith("data-") and key != "data-testid":
                    field = _ALIASES.get(key, key.replace("data-", "").replace("-", "_"))
                    self._current[field] = val

    def handle_endtag(self, tag: str) -> None:
        if self._in_row and tag in ("tr", "div"):
            if self._current:
                self.rows.append(self._current)
            self._in_row = False
            self._current = {}


def _extract_row_selector(selector: str) -> tuple[str, str]:
    """Parse '[data-testid=account-row]' into attr and value."""
    match = re.search(r"\[data-testid=['\"]?([^'\"\]]+)['\"]?\]", selector)
    if match:
        return "data-testid", match.group(1)
    match = re.search(r"\[data-([a-z-]+)=['\"]?([^'\"\]]+)['\"]?\]", selector)
    if match:
        return f"data-{match.group(1)}", match.group(2)
    return "data-testid", ""


def _parse_fixture_rows(html: str, page_key: str, selectors: dict[str, Any]) -> list[dict[str, str]]:
    """Parse HTML fixture using selectors.yaml column_map."""
    page_cfg = selectors.get(page_key, {})
    row_selector = page_cfg.get("table_rows", {}).get("primary", "")
    if not row_selector:
        return []

    attr, value = _extract_row_selector(row_selector.split(",")[0].strip())
    parser = _DataRowParser(attr, value or None)
    parser.feed(html)
    return parser.rows


def load_fixture_html(settings: Settings, name: str) -> str:
    """Load an HTML fixture from tests/fixtures/."""
    path = settings.project_root / "tests" / "fixtures" / name
    return path.read_text(encoding="utf-8")


def scrape_accounts_fixture(settings: Settings) -> list[dict[str, str]]:
    """Parse accounts.html fixture."""
    selectors = load_selectors(settings.selectors_path)
    html = load_fixture_html(settings, "accounts.html")
    return _parse_fixture_rows(html, "accounts", selectors)


def scrape_trades_fixture(settings: Settings, account_id: str = "ACC-001") -> list[dict[str, str]]:
    """Parse trades.html fixture."""
    selectors = load_selectors(settings.selectors_path)
    html = load_fixture_html(settings, "trades.html")
    rows = _parse_fixture_rows(html, "trades", selectors)
    for row in rows:
        row.setdefault("account_id", account_id)
    return rows