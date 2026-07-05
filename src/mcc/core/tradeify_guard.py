"""Tradeify local-only safety guardrails."""
from __future__ import annotations

import structlog

from mcc.core.config import MCCSettings, get_settings, is_cloud_runtime
from mcc.core.exceptions import CloudTradeifyAutomationBlockedError

logger = structlog.get_logger(__name__)


def assert_tradeify_automation_allowed(
    *,
    routine_name: str = "tradeify_browser_automation",
    settings: MCCSettings | None = None,
) -> None:
    """Block Tradeify browser automation in cloud or production runtime."""
    cfg = settings or get_settings()

    blocked_reasons: list[str] = []
    if cfg.is_production:
        blocked_reasons.append(f"APP_ENV={cfg.app_env}")
    if is_cloud_runtime():
        blocked_reasons.append("cloud_runtime_detected")
    if cfg.service_mode in ("web", "worker") and not cfg.is_local:
        blocked_reasons.append(f"SERVICE_MODE={cfg.service_mode}")

    if blocked_reasons:
        logger.error(
            "tradeify_automation_blocked",
            routine=routine_name,
            reasons=blocked_reasons,
            app_env=cfg.app_env,
            service_mode=cfg.service_mode,
        )
        raise CloudTradeifyAutomationBlockedError(
            f"Tradeify browser automation blocked for routine '{routine_name}'",
            details={"reasons": blocked_reasons, "routine": routine_name},
        )