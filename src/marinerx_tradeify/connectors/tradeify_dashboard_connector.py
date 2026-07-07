from __future__ import annotations

"""Tradeify/TFD dashboard connector — read-only metrics via Playwright storage_state."""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .base import TradeifyDashboardMetrics

DEFAULT_DASHBOARD_URL = "https://app.tradeify.co"
DEFAULT_STORAGE_STATE = Path("./data/secure/tradeify_storage_state.json")
LOGIN_PATH_MARKERS = ("/login", "/signin", "/auth", "/sso")


class TradeifyDashboardError(Exception):
    """Dashboard connector error."""


class TradeifySessionError(TradeifyDashboardError):
    """Session missing or expired — reconnect required."""


@dataclass(frozen=True)
class TradeifyDashboardConfig:
    dashboard_url: str = DEFAULT_DASHBOARD_URL
    storage_state_path: Optional[Path] = None
    headless: bool = True
    account_filter: str = "150K"
    timeout_ms: int = 45_000

    @classmethod
    def from_env(cls) -> TradeifyDashboardConfig:
        path = resolve_storage_state_path(os.getenv("TRADEIFY_DASHBOARD_STORAGE_STATE"))
        return cls(
            dashboard_url=os.getenv("TRADEIFY_DASHBOARD_URL", DEFAULT_DASHBOARD_URL),
            storage_state_path=path,
            headless=os.getenv("TRADEIFY_DASHBOARD_HEADLESS", "true").lower() != "false",
            account_filter=os.getenv("TRADEIFY_ACCOUNT_FILTER", "150K"),
            timeout_ms=int(os.getenv("TRADEIFY_DASHBOARD_TIMEOUT_MS", "45000")),
        )


def resolve_storage_state_path(raw: str | None) -> Optional[Path]:
    if not raw or not str(raw).strip():
        return None
    return Path(str(raw).strip())


def _looks_like_login_page(html: str) -> bool:
    lower = html.lower()
    markers = ("sign in", "log in", "login", "password", "mfa", "two-factor", "verify your")
    return sum(1 for m in markers if m in lower) >= 2


def _parse_money(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text.replace(",", ""))
    if not cleaned or cleaned in ("-", "."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"-?\d+", text.replace(",", ""))
    return int(m.group()) if m else None


def parse_dashboard_html(html: str, account_filter: str = "150K") -> list[dict[str, Any]]:
    """Parse account metrics from dashboard HTML (testable without Playwright)."""
    rows: list[dict[str, Any]] = []

    card_pattern = re.compile(
        r'data-account-card[^>]*>(.*?)</(?:div|article|section)>',
        re.IGNORECASE | re.DOTALL,
    )
    cards = card_pattern.findall(html)
    if not cards:
        cards = [html]

    for card in cards:
        label_m = re.search(r'data-account-label="([^"]+)"', card, re.I)
        if not label_m:
            label_m = re.search(r'class="[^"]*account[^"]*name[^"]*"[^>]*>([^<]+)', card, re.I)
        label = (label_m.group(1) if label_m else "").strip()
        if account_filter and account_filter.upper() not in (label + card).upper():
            if "150" not in (label + card).upper():
                continue

        def field(attr: str, fallback: str = "") -> str:
            m = re.search(rf'data-{attr}="([^"]+)"', card, re.I)
            return m.group(1).strip() if m else fallback

        phase = field("phase") or _extract_labeled(card, "phase") or _extract_labeled(card, "status") or "EVALUATION"
        balance = _parse_money(field("balance") or _extract_labeled(card, "balance") or _extract_labeled(card, "equity"))
        daily = _parse_money(field("daily-pnl") or _extract_labeled(card, "daily p&l") or _extract_labeled(card, "daily pnl"))
        profit = _parse_money(field("total-profit") or _extract_labeled(card, "total profit"))
        floor = _parse_money(field("drawdown-floor") or _extract_labeled(card, "drawdown floor"))
        max_dd = _parse_money(field("max-drawdown") or _extract_labeled(card, "max drawdown"))
        winning = _parse_int(field("winning-days") or _extract_labeled(card, "winning days"))
        consistency = _parse_money(field("consistency") or _extract_labeled(card, "consistency"))
        payout_eligible = "eligible" in card.lower() and "payout" in card.lower()
        next_cap = _parse_money(field("next-payout") or _extract_labeled(card, "next payout"))

        rows.append(
            {
                "account_label": label or f"Tradeify {account_filter}",
                "phase": phase.upper(),
                "account_size": 150_000,
                "current_balance": balance,
                "realized_day_pnl": daily,
                "total_profit": profit,
                "max_drawdown_limit": max_dd or 4500.0,
                "drawdown_floor": floor,
                "winning_days": winning,
                "payout_eligible": payout_eligible,
                "next_payout_cap": next_cap or 5000.0,
                "last_payout_status": field("last-payout") or None,
                "consistency_current_pct": consistency,
            }
        )

    return rows


def _extract_labeled(block: str, label: str) -> str:
    pattern = re.compile(rf"{re.escape(label)}\s*[:\-]?\s*\$?([\d,.\-]+)", re.I)
    m = pattern.search(block)
    return m.group(1) if m else ""


def row_to_metrics(row: dict[str, Any]) -> TradeifyDashboardMetrics:
    return TradeifyDashboardMetrics(
        source="tradeify_dashboard",
        account_label=str(row.get("account_label", "Tradeify 150K")),
        phase=str(row.get("phase", "EVALUATION")),
        account_size=int(row.get("account_size", 150_000)),
        current_balance=row.get("current_balance"),
        realized_day_pnl=row.get("realized_day_pnl"),
        total_profit=row.get("total_profit"),
        max_drawdown_limit=row.get("max_drawdown_limit"),
        drawdown_floor=row.get("drawdown_floor"),
        winning_days=row.get("winning_days"),
        payout_eligible=row.get("payout_eligible"),
        next_payout_cap=row.get("next_payout_cap"),
        last_payout_status=row.get("last_payout_status"),
        consistency_current_pct=row.get("consistency_current_pct"),
        raw={"field_names": sorted(row.keys())},
        observed_at=datetime.now(timezone.utc),
    )


class TradeifyDashboardConnector:
    def __init__(self, config: TradeifyDashboardConfig):
        self.config = config

    @property
    def storage_path(self) -> Path:
        return self.config.storage_state_path or DEFAULT_STORAGE_STATE

    def validate_session(self) -> dict[str, Any]:
        path = self.storage_path
        if not path.exists():
            return {
                "dashboard_session_valid": False,
                "status": "reconnect_required",
                "message": "No Tradeify storage_state found. Run tradeify_login_bootstrap locally.",
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "dashboard_session_valid": False,
                "status": "invalid_storage_state",
                "message": "Tradeify storage_state file is unreadable.",
            }
        cookies = data.get("cookies") or []
        if not cookies:
            return {
                "dashboard_session_valid": False,
                "status": "expired",
                "message": "Tradeify session has no cookies — re-authenticate.",
            }
        return {
            "dashboard_session_valid": True,
            "status": "ok",
            "message": "Storage state present.",
            "cookie_count": len(cookies),
        }

    async def ensure_login(self) -> None:
        from mcc.core.tradeify_guard import assert_tradeify_automation_allowed

        assert_tradeify_automation_allowed(routine_name="tradeify_dashboard_scrape")
        session = self.validate_session()
        if not session.get("dashboard_session_valid"):
            raise TradeifySessionError(session.get("message", "Reconnect required"))

    async def scrape_account_cards(self) -> list[dict[str, Any]]:
        session = self.validate_session()
        if not session.get("dashboard_session_valid"):
            raise TradeifySessionError(session.get("message", "Reconnect required"))

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise TradeifyDashboardError(
                "Playwright not installed. pip install playwright && playwright install chromium"
            ) from exc

        from mcc.core.tradeify_guard import assert_tradeify_automation_allowed

        assert_tradeify_automation_allowed(routine_name="tradeify_dashboard_scrape")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.config.headless)
            context = await browser.new_context(storage_state=str(self.storage_path))
            page = await context.new_page()
            try:
                await page.goto(
                    self.config.dashboard_url,
                    wait_until="domcontentloaded",
                    timeout=self.config.timeout_ms,
                )
                html = await page.content()
                if _looks_like_login_page(html):
                    raise TradeifySessionError("Tradeify session expired — run login bootstrap again.")
                rows = parse_dashboard_html(html, self.config.account_filter)
                if not rows:
                    raise TradeifyDashboardError("No account cards matched filter on dashboard.")
                return rows
            finally:
                await context.close()
                await browser.close()

    async def fetch_metrics(self) -> TradeifyDashboardMetrics:
        rows = await self.scrape_account_cards()
        return row_to_metrics(rows[0])