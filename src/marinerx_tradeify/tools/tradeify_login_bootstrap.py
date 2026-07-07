"""Manual Playwright login bootstrap for Tradeify dashboard sessions.

Opens a headed browser so the user can log in and complete MFA manually.
Saves Playwright ``storage_state`` to the path configured by
``TRADEIFY_DASHBOARD_STORAGE_STATE`` (never logs credentials).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import structlog

from marinerx_tradeify.connectors.tradeify_dashboard_connector import (
    DEFAULT_DASHBOARD_URL,
    DEFAULT_STORAGE_STATE,
    LOGIN_PATH_MARKERS,
    TradeifyDashboardConfig,
    _looks_like_login_page,
    resolve_storage_state_path,
)

logger = structlog.get_logger(__name__)

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a Tradeify dashboard browser session (manual login + MFA).",
    )
    parser.add_argument(
        "--dashboard-url",
        default=os.getenv("TRADEIFY_DASHBOARD_URL", DEFAULT_DASHBOARD_URL),
        help="Tradeify dashboard base URL (default: TRADEIFY_DASHBOARD_URL or app.tradeify.co).",
    )
    parser.add_argument(
        "--storage-state",
        default=os.getenv("TRADEIFY_DASHBOARD_STORAGE_STATE", ""),
        help="Output path for Playwright storage_state JSON (default: TRADEIFY_DASHBOARD_STORAGE_STATE).",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=int(os.getenv("TRADEIFY_DASHBOARD_BOOTSTRAP_TIMEOUT_MS", "600000")),
        help="Max wait for manual login completion in milliseconds (default: 600000).",
    )
    return parser.parse_args(argv)


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            path.parent.chmod(0o700)
        except OSError:
            logger.warning("storage_state_dir_chmod_failed", path=str(path.parent))


async def _wait_for_dashboard(page, timeout_ms: int) -> bool:
    """Poll until the page no longer looks like a login screen."""
    deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000.0)
    while asyncio.get_event_loop().time() < deadline:
        html = await page.content()
        url = page.url.lower()
        on_login_path = any(marker in url for marker in LOGIN_PATH_MARKERS)
        if not on_login_path and not _looks_like_login_page(html):
            return True
        await asyncio.sleep(2.0)
    return False


async def run_bootstrap(
    *,
    dashboard_url: str,
    storage_state_path: Path,
    timeout_ms: int,
) -> int:
    """Open headed browser, wait for manual login, persist storage_state."""
    if not PLAYWRIGHT_AVAILABLE:
        print(
            "Playwright is not installed. Install with: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 1

    from mcc.core.tradeify_guard import assert_tradeify_automation_allowed

    assert_tradeify_automation_allowed(routine_name="tradeify_login_bootstrap")

    _ensure_parent_dir(storage_state_path)

    print("Tradeify login bootstrap")
    print(f"  Dashboard URL : {dashboard_url}")
    print(f"  Storage state : {storage_state_path}")
    print()
    print("A browser window will open. Log in manually and complete MFA if prompted.")
    print("Do not close the browser until login finishes — the tool will detect the dashboard.")
    print("Credentials are never logged or stored in plaintext by this tool.")
    print()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(dashboard_url, wait_until="domcontentloaded", timeout=60_000)
            logged_in = await _wait_for_dashboard(page, timeout_ms)
            if not logged_in:
                print(
                    "Timed out waiting for dashboard after login. "
                    "Re-run bootstrap and complete MFA before the timeout.",
                    file=sys.stderr,
                )
                return 2

            await context.storage_state(path=str(storage_state_path))
            if os.name != "nt":
                try:
                    storage_state_path.chmod(0o600)
                except OSError:
                    logger.warning("storage_state_chmod_failed", path=str(storage_state_path))

            print()
            print("Session saved successfully.")
            print(f"  Storage state : {storage_state_path}")
            print("Headless sync can now use this session via TradeifyDashboardConnector.")
            return 0
        finally:
            await context.close()
            await browser.close()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    storage_path = resolve_storage_state_path(
        args.storage_state or os.getenv("TRADEIFY_DASHBOARD_STORAGE_STATE"),
    )
    if storage_path is None:
        storage_path = DEFAULT_STORAGE_STATE

    config = TradeifyDashboardConfig(
        dashboard_url=args.dashboard_url,
        storage_state_path=storage_path,
        headless=False,
    )
    logger.info(
        "tradeify_login_bootstrap_start",
        dashboard_url=config.dashboard_url,
        storage_state_path=str(config.storage_state_path),
    )

    return asyncio.run(
        run_bootstrap(
            dashboard_url=config.dashboard_url,
            storage_state_path=config.storage_state_path or DEFAULT_STORAGE_STATE,
            timeout_ms=args.timeout_ms,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())