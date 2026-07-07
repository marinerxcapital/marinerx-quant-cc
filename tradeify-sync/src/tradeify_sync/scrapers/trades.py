"""Trade history scraper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tradeify_sync.scrapers.base import BaseScraper


class TradesScraper(BaseScraper):
    """Extract trade history (export-first, DOM fallback)."""

    async def scrape_trades(
        self,
        account_id: str,
        since_utc: datetime | None,
        backfill_days: int,
    ) -> dict[str, Any]:
        """Scrape trades for an account; returns csv path or rows."""
        await self.goto("trades")
        self.logger.info(
            "scrape_trades",
            account_id=account_id,
            since=str(since_utc),
            backfill_days=backfill_days,
        )

        csv_path = await self.try_export("trades")
        if csv_path:
            return {"csv": csv_path, "account_id": account_id}

        rows = await self.extract_rows("trades")
        for row in rows:
            row.setdefault("account_id", account_id)
        return {"rows": rows, "account_id": account_id}

    async def scrape_fills(
        self,
        account_id: str,
        since_utc: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Fills view not universally available — return empty."""
        self.logger.info("fills_unavailable", account_id=account_id)
        return []