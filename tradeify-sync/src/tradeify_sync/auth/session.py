"""Session persistence helpers."""

from __future__ import annotations

from pathlib import Path

from tradeify_sync.browser.guards import assert_navigable
from tradeify_sync.browser.manager import BrowserManager
from tradeify_sync.config import Settings, load_selectors
from tradeify_sync.utils.logging import get_logger

logger = get_logger(__name__)


def session_state_path(settings: Settings) -> Path:
    """Return the path to storage_state.json."""
    return settings.resolve(settings.browser.session_path)


def has_session(settings: Settings) -> bool:
    """Return True if a persisted session file exists."""
    return session_state_path(settings).exists()


async def is_session_valid(bm: BrowserManager, settings: Settings) -> bool:
    """Check whether the persisted session is still valid."""
    if not has_session(settings):
        return False
    selectors = load_selectors(settings.selectors_path)
    marker_sel = selectors.get("login", {}).get("logged_in_marker", {}).get("primary", "")
    if not marker_sel:
        return False

    url = settings.page_url("dashboard")
    assert_navigable(url, settings.tradeify.base_url)
    page = bm.page
    try:
        await page.goto(url, wait_until="domcontentloaded")
        marker = page.locator(marker_sel).first
        await marker.wait_for(state="visible", timeout=5000)
        logger.info("session_valid")
        return True
    except Exception:
        logger.info("session_invalid")
        return False


async def persist_session(bm: BrowserManager) -> None:
    """Persist current browser storage state."""
    await bm.close()


async def clear_session(settings: Settings) -> None:
    """Remove persisted session file."""
    path = session_state_path(settings)
    if path.exists():
        path.unlink()
        logger.info("session_cleared")