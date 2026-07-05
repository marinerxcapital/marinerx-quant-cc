"""Tests for regime/hmm.py statsmodels swap."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from mcc.core.events import RegimeEvent
from mcc.regime.hmm import (
    FIXTURE_HMM_N_OBS,
    build_regime_event,
    classify_regime,
    hmmlearn_baseline_compare,
)


def _fixture_prices() -> pd.Series:
    from mcc.regime.hmm import _fixture_two_regime_prices

    return _fixture_two_regime_prices(n=FIXTURE_HMM_N_OBS)


def test_classify_regime_output_shape():
    result = classify_regime(_fixture_prices())
    assert "state" in result
    assert "confidence" in result
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["state"] in ("trending", "mean-reverting", "regime_0", "regime_1")


def test_build_regime_event_contract():
    ev = build_regime_event(_fixture_prices(), symbol="NQ")
    assert isinstance(ev, RegimeEvent)
    assert ev.payload["type"] == "regime"
    assert ev.payload["symbol"] == "NQ"
    assert "state" in ev.payload
    assert "confidence" in ev.payload


def test_hmmlearn_baseline_compare_document(tmp_path: Path):
    comparison = hmmlearn_baseline_compare(_fixture_prices())
    assert "statsmodels" in comparison
    assert "hmmlearn" in comparison
    assert comparison["fixture"]["n_obs"] == FIXTURE_HMM_N_OBS
    out = tmp_path / "regime_old_vs_new_comparison.json"
    out.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    assert out.stat().st_size > 100