from __future__ import annotations

"""Tradeify/TFD dashboard connector skeleton.

Use this only when Tradeify does not expose an official API for prop-firm metrics.
The connector must operate on the user's own dashboard session, with credentials stored in
a secret manager or manually established Playwright storage state.

Security constraints:
- Do not hardcode credentials.
- Do not print dashboard HTML containing private account details.
- Store screenshots only when MARINERX_DEBUG_DASHBOARD_SNAPSHOTS=true.
- Prefer read-only metrics extraction. No payout requests or profile changes.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .base import TradeifyDashboardMetrics


@dataclass(frozen=True)
class TradeifyDashboardConfig:
    dashboard_url: str = "https://app.tradeify.co"
    storage_state_path: Optional[Path] = None
    headless: bool = True
    account_filter: str = "150K"
    timeout_ms: int = 45_000


class TradeifyDashboardConnector:
    def __init__(self, config: TradeifyDashboardConfig):
        self.config = config

    async def ensure_login(self) -> None:
        """Ensure an authenticated browser context exists.

        Grok implementation requirements:
        - Use Playwright.
        - If storage_state is missing/expired, run an interactive login helper locally.
        - Support MFA/manual approval without attempting to bypass it.
        - Save storage_state encrypted or in a protected local path.
        - Never send credentials to logs, model prompts, or remote telemetry.
        """
        raise NotImplementedError("Implement Playwright authenticated session handling.")

    async def scrape_account_cards(self) -> list[dict[str, Any]]:
        """Scrape account cards/table rows from the user's Tradeify/TFD dashboard.

        Expected raw fields to locate where available:
        - account label/name
        - phase/status: evaluation, funded, payout pending, failed, active
        - current balance/equity
        - daily PnL
        - total profit
        - drawdown floor/headroom
        - winning days
        - payout eligibility
        - next payout cap/status
        - consistency percentage during evaluation
        """
        raise NotImplementedError("Implement selectors with resilient text-based fallbacks.")

    async def fetch_metrics(self) -> TradeifyDashboardMetrics:
        """Return normalized Tradeify dashboard metrics for the configured 150K account."""
        rows = await self.scrape_account_cards()
        if not rows:
            raise RuntimeError("No Tradeify dashboard account rows found.")

        # Grok should replace this with robust account selection and parsing.
        row = rows[0]
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
        )
