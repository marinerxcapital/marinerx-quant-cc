"""Read-only navigation and interaction guards."""

from __future__ import annotations

import re
from typing import Any, Protocol
from urllib.parse import urlparse

from tradeify_sync.constants import (
    MUTATING_INTERACTION_DENYLIST,
    URL_ALLOWLIST_PATTERNS,
    MutatingInteractionBlocked,
    NavigationError,
)
from tradeify_sync.utils.logging import get_logger

logger = get_logger(__name__)

_PATH_PATTERNS = [
    r"^/?$",
    r"^/login",
    r"^/auth",
    r"^/dashboard",
    r"^/accounts",
    r"^/trades",
    r"^/history",
    r"^/positions",
    r"^/payouts",
]


class ElementDescriptor(Protocol):
    """Minimal element interface for guard testing."""

    def inner_text(self) -> str: ...

    def get_attribute(self, name: str) -> str | None: ...


_ATTR_KEYS = ("aria-label", "name", "id", "value", "type", "title", "data-action")

_ASSET_SUFFIXES = (".js", ".css", ".woff", ".woff2", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".json", ".map", ".webp")
_ASSET_PREFIXES = ("/_next/", "/static/", "/assets/", "/fonts/", "/api/", "/favicon", "/images/")


def is_same_host_asset(url: str, allowed_base_url: str) -> bool:
    """Allow static/API subresources from the dashboard host (SPA needs JS bundles)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        return False
    base_host = urlparse(allowed_base_url).netloc.lower()
    if parsed.netloc.lower() != base_host:
        return False
    path = parsed.path.lower()
    if path.endswith(_ASSET_SUFFIXES):
        return True
    return any(path.startswith(prefix) for prefix in _ASSET_PREFIXES)


def assert_navigable(url: str, allowed_base_url: str | None = None) -> None:
    """Raise NavigationError unless url matches the allowlist."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        logger.warning("navigation_denied", url=url, reason="non-https")
        raise NavigationError(f"URL not on allowlist: {url}")

    if allowed_base_url:
        base_host = urlparse(allowed_base_url).netloc.lower()
        if parsed.netloc.lower() != base_host:
            logger.warning("navigation_denied", url=url, reason="host-mismatch")
            raise NavigationError(f"URL not on allowlist: {url}")
    elif not (
        parsed.netloc.lower().endswith("tradeify.example")
        or parsed.netloc.lower().endswith("tradeify.co")
    ):
        logger.warning("navigation_denied", url=url, reason="unknown-host")
        raise NavigationError(f"URL not on allowlist: {url}")

    path = parsed.path.rstrip("/") or "/"
    for pattern in _PATH_PATTERNS:
        if re.match(pattern, path, re.IGNORECASE):
            logger.info("navigation_allowed", url=url, pattern=pattern)
            return

    for pattern in URL_ALLOWLIST_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            logger.info("navigation_allowed", url=url, pattern=pattern)
            return

    logger.warning("navigation_denied", url=url)
    raise NavigationError(f"URL not on allowlist: {url}")


def _collect_descriptor_text(descriptor: ElementDescriptor | dict[str, str]) -> str:
    if isinstance(descriptor, dict):
        parts = [descriptor.get("text", "")]
        for key in _ATTR_KEYS:
            val = descriptor.get(key)
            if val:
                parts.append(val)
        return " ".join(parts).lower()

    parts: list[str] = []
    try:
        parts.append(descriptor.inner_text())
    except Exception:
        pass
    for key in _ATTR_KEYS:
        try:
            val = descriptor.get_attribute(key)
            if val:
                parts.append(val)
        except Exception:
            pass
    return " ".join(parts).lower()


def assert_non_mutating(descriptor: ElementDescriptor | dict[str, str]) -> None:
    """Raise MutatingInteractionBlocked if descriptor matches denylist."""
    text = _collect_descriptor_text(descriptor)
    for pattern in MUTATING_INTERACTION_DENYLIST:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("interaction_denied", pattern=pattern)
            raise MutatingInteractionBlocked(
                f"Mutating interaction blocked (matched '{pattern}'): {text[:80]}"
            )
    logger.info("interaction_allowed")


async def guarded_click(page: Any, locator: Any) -> None:
    """Assert non-mutating then click via Playwright locator."""
    element = await locator.element_handle()
    if element is None:
        raise NavigationError("Element not found for guarded click")

    text = await locator.inner_text()
    attrs: dict[str, str] = {"text": text}
    for key in _ATTR_KEYS:
        val = await locator.get_attribute(key)
        if val:
            attrs[key] = val
    assert_non_mutating(attrs)
    await locator.click()