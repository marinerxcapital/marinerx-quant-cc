"""Trade history scraper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tradeify_sync.constants import SelectorResolutionError
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
        await self.page.wait_for_timeout(8000)
        self.logger.info(
            "scrape_trades",
            account_id=account_id,
            since=str(since_utc),
            backfill_days=backfill_days,
        )

        csv_path = await self.try_export("trades")
        if csv_path:
            return {"csv": csv_path, "account_id": account_id}

        try:
            rows = await self.extract_rows("trades")
        except SelectorResolutionError:
            rows = await self._extract_trade_log_rows()
        for row in rows:
            row.setdefault("account_id", account_id)
        if not rows:
            self.logger.info("trade_log_empty", account_id=account_id)
        return {"rows": rows, "account_id": account_id}

    async def _extract_trade_log_rows(self) -> list[dict[str, str]]:
        """Fallback: parse trade-log table if selectors.yaml does not match TFD UI."""
        for sel in ("table tbody tr", "table tr", "[role='row']"):
            locator = self.page.locator(sel)
            count = await locator.count()
            if count < 2:
                continue
            rows: list[dict[str, str]] = []
            for i in range(count):
                row = locator.nth(i)
                cells = row.locator("td")
                n = await cells.count()
                if n < 4:
                    continue
                texts = [(await cells.nth(j).inner_text()).strip() for j in range(n)]
                if not any(texts) or texts[0].lower() in ("date", "time", "symbol"):
                    continue
                rows.append(
                    {
                        "trade_id": texts[0],
                        "symbol_raw": texts[1] if n > 1 else "",
                        "side": texts[2] if n > 2 else "",
                        "qty": texts[3] if n > 3 else "1",
                        "entry_price": texts[4] if n > 4 else "",
                        "exit_price": texts[5] if n > 5 else "",
                        "gross_pnl": texts[6] if n > 6 else "",
                    }
                )
            if rows:
                self.logger.info("trade_log_table_ok", rows=len(rows))
                return rows
        return []

    async def scrape_fills(
        self,
        account_id: str,
        since_utc: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Fills view not universally available — return empty."""
        self.logger.info("fills_unavailable", account_id=account_id)
        return []