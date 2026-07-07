"""Account scraper."""

from __future__ import annotations

from tradeify_sync.constants import SelectorResolutionError
from tradeify_sync.scrapers.base import BaseScraper
from tradeify_sync.scrapers.tfd_parser import parse_accounts_from_text


class AccountsScraper(BaseScraper):
    """Extract account rows from the dashboard."""

    async def scrape_accounts(self) -> list[dict[str, str]]:
        """Return raw account dict rows."""
        await self.goto("accounts")
        await self.page.wait_for_timeout(8000)
        try:
            rows = await self.extract_rows("accounts")
            if rows:
                return rows
        except SelectorResolutionError:
            pass
        text = await self.page.inner_text("body")
        parsed = parse_accounts_from_text(text)
        if parsed:
            self.logger.info("tfd_text_parse_ok", accounts=len(parsed))
            return parsed
        await self.fail_shot("accounts", "no account rows via selectors or TFD parser")
        return []