"""System truth endpoints — version, config check, operational state, data freshness."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from mcc.core.config import get_settings
from mcc.system.state import (
    build_config_check,
    build_data_freshness,
    build_system_state,
    build_version_info,
)

router = APIRouter(tags=["system"])


@router.get("/version")
def version() -> dict[str, Any]:
    return build_version_info()


@router.get("/config-check")
def config_check() -> dict[str, Any]:
    return build_config_check()


@router.get("/api/system-state")
def system_state() -> dict[str, Any]:
    return build_system_state()


@router.get("/api/data-freshness")
def data_freshness() -> dict[str, Any]:
    return build_data_freshness()