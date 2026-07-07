"""Playwright browser manager with read-only hooks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from tradeify_sync.browser.guards import assert_navigable, is_same_host_asset
from tradeify_sync.config import Settings
from tradeify_sync.utils.logging import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Wraps Playwright persistent context with session persistence."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> BrowserManager:
        await self.launch()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not launched")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Browser not launched")
        return self._context

    async def launch(self) -> None:
        """Launch persistent chromium context."""
        self._playwright = await async_playwright().start()
        profile_dir = self.settings.resolve("data/sessions/profile")
        profile_dir.mkdir(parents=True, exist_ok=True)
        downloads = self.settings.resolve("data/downloads")
        downloads.mkdir(parents=True, exist_ok=True)

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=self.settings.browser.headless,
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._context.set_default_timeout(self.settings.browser.timeout_ms)

        self._context.on("page", self._on_new_page)
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()
        await self._register_guards(self._page)

    async def _on_new_page(self, page: Page) -> None:
        await self._register_guards(page)

    async def _register_guards(self, page: Page) -> None:
        async def _route_handler(route: Any) -> None:
            url = route.request.url
            try:
                if is_same_host_asset(url, self.settings.tradeify.base_url):
                    await route.continue_()
                    return
                assert_navigable(url, self.settings.tradeify.base_url)
                await route.continue_()
            except Exception:
                logger.warning("route_blocked", url=url)
                await route.abort()

        await page.route("**/*", _route_handler)

    async def close(self) -> None:
        """Persist session and close browser."""
        if self._context and self.settings.browser.persist_session:
            storage_path = self.settings.resolve(self.settings.browser.session_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(storage_path))
            logger.info("session_persisted", path=str(storage_path))
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._context = None
        self._page = None
        self._playwright = None