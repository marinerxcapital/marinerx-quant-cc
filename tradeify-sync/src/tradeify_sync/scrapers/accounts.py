"""Account scraper."""

from __future__ import annotations

from typing import Any

from tradeify_sync.scrapers.base import BaseScraper


class AccountsScraper(BaseScraper):
    """Extract account rows from the dashboard."""

    async def scrape_accounts(self) -> list[dict[str, str]]:
        """Return raw account dict rows."""
        await self.goto("accounts")
        return await self.extract_rows("accounts")