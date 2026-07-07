"""Shared constants and exception hierarchy."""

from __future__ import annotations

from decimal import Decimal

# ---------------------------------------------------------------------------
# Exception hierarchy (Master Brief §4.3)
# ---------------------------------------------------------------------------


class TradeifySyncError(Exception):
    """Base exception for all tradeify-sync errors."""


class ConfigError(TradeifySyncError):
    """Invalid configuration."""


class AuthError(TradeifySyncError):
    """Authentication or session failure."""


class NavigationError(TradeifySyncError):
    """Navigation blocked or failed."""


class MutatingInteractionBlocked(NavigationError):
    """A mutating UI interaction was blocked by read-only guards."""


class ExtractionError(TradeifySyncError):
    """Data extraction failure."""


class SelectorResolutionError(TradeifySyncError):
    """DOM selector could not be resolved."""

    def __init__(self, page_key: str, selector_key: str, message: str | None = None) -> None:
        self.page_key = page_key
        self.selector_key = selector_key
        detail = message or f"Could not resolve selector '{selector_key}' on page '{page_key}'"
        super().__init__(detail)


class IntegrityError(TradeifySyncError):
    """Data integrity or normalization failure."""


# ---------------------------------------------------------------------------
# Read-only safety patterns (C1)
# ---------------------------------------------------------------------------

URL_ALLOWLIST_PATTERNS: list[str] = [
    r"^https://[^/]+/?$",
    r"^https://[^/]+/login",
    r"^https://[^/]+/dashboard",
    r"^https://[^/]+/accounts",
    r"^https://[^/]+/trades",
    r"^https://[^/]+/history",
    r"^https://[^/]+/positions",
    r"^https://[^/]+/payouts",
]

MUTATING_INTERACTION_DENYLIST: list[str] = [
    r"\bbuy\b",
    r"\bsell\b",
    r"submit order",
    r"place order",
    r"close position",
    r"\bflatten\b",
    r"\bliquidate\b",
    r"\bwithdraw\b",
    r"request payout",
    r"reset account",
    r"\bdelete\b",
    r"save settings",
    r"\bconfirm\b",
]

# Fallback instrument specs (overridden by config at runtime)
INSTRUMENT_ROOTS: dict[str, tuple[Decimal, Decimal]] = {
    "NQ": (Decimal("0.25"), Decimal("5.00")),
    "ES": (Decimal("0.25"), Decimal("12.50")),
    "CL": (Decimal("0.01"), Decimal("10.00")),
    "GC": (Decimal("0.10"), Decimal("10.00")),
    "MNQ": (Decimal("0.25"), Decimal("0.50")),
    "MES": (Decimal("0.25"), Decimal("1.25")),
}