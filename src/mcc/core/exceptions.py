"""Core exceptions enforcing safety gates."""
from __future__ import annotations
from typing import Any

class MCCError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(MCCError):
    pass


class RiskVeto(MCCError):
    pass


class ExecutionBlocked(MCCError):
    pass


class AgentError(MCCError):
    pass


class BusError(MCCError):
    pass


class ConfigError(MCCError):
    pass


class DataError(MCCError):
    pass


class FeedError(MCCError):
    pass


class IntegrityError(MCCError):
    pass


class AnalyticsValidationError(MCCError):
    pass


class AnalyticsConversionError(MCCError):
    pass
