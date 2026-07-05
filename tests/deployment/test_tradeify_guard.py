import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mcc.core.config import MCCSettings
from mcc.core.exceptions import CloudTradeifyAutomationBlockedError
from mcc.core.tradeify_guard import assert_tradeify_automation_allowed


def test_blocks_production_env():
    settings = MCCSettings(_env_file=None, APP_ENV="production", SERVICE_MODE="worker")
    with pytest.raises(CloudTradeifyAutomationBlockedError):
        assert_tradeify_automation_allowed(settings=settings)


def test_blocks_cloud_runtime(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    settings = MCCSettings(_env_file=None, APP_ENV="local", SERVICE_MODE="web")
    with pytest.raises(CloudTradeifyAutomationBlockedError):
        assert_tradeify_automation_allowed(settings=settings)
    monkeypatch.delenv("RENDER", raising=False)


def test_allows_local_dev():
    settings = MCCSettings(_env_file=None, APP_ENV="local", SERVICE_MODE="web")
    assert_tradeify_automation_allowed(settings=settings)