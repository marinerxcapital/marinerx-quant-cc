"""Test read-only guards."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tradeify_sync.browser.guards import (
    assert_navigable,
    assert_non_mutating,
)
from tradeify_sync.constants import (
    MUTATING_INTERACTION_DENYLIST,
    MutatingInteractionBlocked,
    NavigationError,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://dashboard.tradeify.example/",
        "https://dashboard.tradeify.example/login",
        "https://dashboard.tradeify.example/accounts",
        "https://dashboard.tradeify.example/trades",
        "https://dashboard.tradeify.example/positions",
        "https://dashboard.tradeify.example/payouts",
    ],
)
def test_allowlisted_urls_pass(url: str) -> None:
    assert_navigable(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/accounts",
        "http://dashboard.tradeify.example/accounts",
        "https://dashboard.tradeify.example/orders/place",
    ],
)
def test_non_allowlisted_urls_denied(url: str) -> None:
    with pytest.raises(NavigationError):
        assert_navigable(url)


@pytest.mark.parametrize(
    "descriptor",
    [
        {"text": "Buy NQ"},
        {"text": "Sell ES"},
        {"text": "Withdraw funds"},
        {"text": "Reset account"},
        {"text": "Close position now"},
        {"text": "Flatten all"},
        {"text": "Liquidate"},
    ],
)
def test_mutating_descriptors_blocked(descriptor: dict[str, str]) -> None:
    with pytest.raises(MutatingInteractionBlocked):
        assert_non_mutating(descriptor)


def test_benign_descriptor_passes() -> None:
    assert_non_mutating({"text": "Next page", "aria-label": "Go to next page"})


def test_scrapers_use_guarded_click_only() -> None:
    """Ensure scraper code does not call .click( directly."""
    root = Path(__file__).resolve().parents[1]
    scraper_dir = root / "src" / "tradeify_sync" / "scrapers"
    violations: list[str] = []
    for py_file in scraper_dir.glob("*.py"):
        if py_file.name == "fixtures.py":
            continue
        content = py_file.read_text(encoding="utf-8")
        # guarded_click is imported and used; direct .click( is forbidden
        for match in re.finditer(r"\.click\(", content):
            line_start = content.rfind("\n", 0, match.start()) + 1
            line = content[line_start : content.find("\n", match.start())]
            if "guarded_click" not in line:
                violations.append(f"{py_file.name}: {line.strip()}")
    assert violations == [], f"Direct .click() found: {violations}"