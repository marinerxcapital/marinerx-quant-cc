"""Base scraper with read-only extraction."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tradeify_sync.browser.guards import assert_navigable, guarded_click
from tradeify_sync.browser.humanize import human_pause
from tradeify_sync.config import Settings
from tradeify_sync.constants import ExtractionError, SelectorResolutionError
from tradeify_sync.utils.logging import get_logger

MAX_PAGES = 50


class BaseScraper:
    """Common scraper functionality for DOM extraction."""

    def __init__(
        self,
        page: Any,
        settings: Settings,
        selectors: dict[str, Any],
        logger: Any | None = None,
    ) -> None:
        self.page = page
        self.settings = settings
        self.selectors = selectors
        self.logger = logger or get_logger(self.__class__.__name__)

    async def goto(self, page_key: str) -> None:
        """Navigate to a dashboard page (allowlist-checked)."""
        url = self.settings.page_url(page_key)
        assert_navigable(url, self.settings.tradeify.base_url)
        await self.page.goto(url, wait_until="domcontentloaded")
        await human_pause(self.settings)

    async def resolve(self, page_key: str, selector_key: str) -> Any:
        """Resolve a selector from selectors.yaml."""
        page_cfg = self.selectors.get(page_key, {})
        entry = page_cfg.get(selector_key)
        if not entry or not isinstance(entry, dict):
            raise SelectorResolutionError(page_key, selector_key)

        candidates = [entry.get("primary", "")] + list(entry.get("fallbacks", []))
        wait_mode = entry.get("wait", "visible")
        timeout = self.settings.browser.timeout_ms

        for sel in candidates:
            if not sel:
                continue
            locator = self.page.locator(sel).first
            try:
                await locator.wait_for(state=wait_mode, timeout=timeout)
                self.logger.info("selector_resolved", page=page_key, key=selector_key)
                return locator
            except Exception:
                continue
        raise SelectorResolutionError(page_key, selector_key)

    async def try_export(self, page_key: str) -> Path | None:
        """Attempt native CSV export if configured."""
        page_cfg = self.selectors.get(page_key, {})
        if "export_button" not in page_cfg:
            return None
        try:
            btn = await self.resolve(page_key, "export_button")
        except SelectorResolutionError:
            return None

        downloads = self.settings.resolve("data/downloads")
        downloads.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        dest = downloads / f"{page_key}_{ts}.csv"

        async with self.page.expect_download() as dl_info:
            await guarded_click(self.page, btn)
        download = await dl_info.value
        await download.save_as(str(dest))
        self.logger.info("export_downloaded", path=str(dest))
        return dest

    async def extract_rows(self, page_key: str) -> list[dict[str, str]]:
        """Extract table rows using column_map from selectors."""
        page_cfg = self.selectors.get(page_key, {})
        column_map: dict[str, Any] = page_cfg.get("column_map", {})
        all_rows: list[dict[str, str]] = []
        pages = 0

        while pages < MAX_PAGES:
            pages += 1
            rows_locator = await self.resolve(page_key, "table_rows")
            count = await rows_locator.count()
            for i in range(count):
                row = rows_locator.nth(i)
                raw: dict[str, str] = {}
                for field, spec in column_map.items():
                    if isinstance(spec, dict) and "selector" in spec:
                        cell = row.locator(spec["selector"]).first
                        raw[field] = (await cell.inner_text()).strip()
                    elif isinstance(spec, dict) and "index" in spec:
                        cells = row.locator("td")
                        idx = int(spec["index"])
                        if await cells.count() > idx:
                            raw[field] = (await cells.nth(idx).inner_text()).strip()
                        else:
                            raw[field] = ""
                    else:
                        raw[field] = ""
                all_rows.append(raw)

            if "pagination_next" not in page_cfg:
                break
            try:
                next_btn = await self.resolve(page_key, "pagination_next")
                if not await next_btn.is_enabled():
                    break
                await guarded_click(self.page, next_btn)
                await human_pause(self.settings)
            except SelectorResolutionError:
                break

        return all_rows

    async def fail_shot(self, page_key: str, context: str) -> None:
        """Capture screenshot and raise ExtractionError."""
        shots = self.settings.resolve("screenshots")
        shots.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        path = shots / f"{page_key}_{ts}.png"
        await self.page.screenshot(path=str(path))
        self.logger.error("extraction_failed", page=page_key, context=context, screenshot=str(path))
        raise ExtractionError(f"Extraction failed on {page_key}: {context}")