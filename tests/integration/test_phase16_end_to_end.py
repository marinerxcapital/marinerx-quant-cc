"""Phase 16 integration tests — full pipelines + contract regression."""
from __future__ import annotations

import json
import re
from datetime import timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mcc.core.events import DecisionEvent, RegimeEvent
from mcc.core.exceptions import AnalyticsValidationError
from mcc.decision.engine import decide
from mcc.performance.analytics import compose_performance_report
from mcc.performance.quantstats_adapter import fixture_trades
from mcc.regime.hmm import build_regime_event, hmmlearn_baseline_compare
from mcc.risk.monitor import RiskState
from mcc.risk.prop_guardian import RiskLevel
from mcc.risk.portfolio import optimize_allocation
from mcc.risk.riskfolio_adapter import _RISKFOLIO_AVAILABLE


REPORTS_ROOT = Path("reports_out")


def test_riskstate_schema_unchanged():
    rs = RiskState(
        ts_utc=pd.Timestamp("2024-01-01", tz=timezone.utc).to_pydatetime(),
        source="RiskCommand",
        equity=Decimal("100000"),
        risk_level=RiskLevel.OK,
        position_size=2,
        size_reason="test",
        var=0.02,
        es=0.03,
        var_breach=False,
        exposure_gross=Decimal("30000"),
        exposure_net=Decimal("10000"),
        veto=False,
        veto_reason="",
        details={},
    )
    d = rs.to_dict()
    required = {
        "ts_utc", "source", "equity", "risk_level", "position_size", "size_reason",
        "var", "es", "var_breach", "exposure_gross", "exposure_net", "veto", "veto_reason", "details",
    }
    assert required.issubset(d.keys())


def test_decision_event_contract_unchanged():
    from datetime import datetime

    ev = DecisionEvent(datetime.now(timezone.utc), "DecisionEngine", "NQ", "GO", "clean", 2)
    assert ev.payload == {"symbol": "NQ", "decision": "GO", "reason": "clean", "size": 2}


def test_decide_regression_unmodified():
    d = decide(has_green_strategy=True, risk_veto=False, data_ok=True, session_ok=True)
    assert d["decision"] == "GO"


def test_validation_failure_raises_not_nan():
    idx = pd.date_range("2024-06-01", periods=5, freq="D", tz=timezone.utc)
    bad = pd.Series([0.01, np.nan, 0.02, 0.0, 0.01], index=idx)
    with pytest.raises(AnalyticsValidationError):
        from mcc.analytics.validation import validate_return_series

        validate_return_series(bad)


@pytest.mark.skipif(not _RISKFOLIO_AVAILABLE, reason="riskfolio-lib not installed")
def test_allocation_pipeline_writes_json(tmp_path: Path):
    rng = np.random.default_rng(7)
    idx = pd.date_range("2024-01-02", periods=100, freq="B", tz=timezone.utc)
    returns = pd.DataFrame({s: rng.normal(0.0003, 0.01, 100) for s in ("NQ", "ES", "CL", "GC")}, index=idx)
    result = optimize_allocation(returns, account_id="e2e_acct", export_json=True, output_dir=tmp_path)
    json_files = list(tmp_path.glob("*.json"))
    assert result.weights
    assert len(json_files) >= 1
    total = sum(float(w) for w in result.weights.values())
    assert abs(total - 1.0) < 0.05


def test_tearsheet_e2e_pipeline(tmp_path: Path):
    out = tmp_path / "tear_sheets"
    report = compose_performance_report(
        fixture_trades(),
        strategy_id="STR-E2E-001",
        out_dir=out,
    )
    html = Path(report["tearsheet_path"])
    assert html.exists() and html.stat().st_size > 500
    assert report["metrics"]["benchmark"].startswith("flat_rate")
    assert report["attribution"]["go_count"] >= 1


def test_regime_comparison_export():
    comparison = hmmlearn_baseline_compare()
    diag_dir = REPORTS_ROOT / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    path = diag_dir / "regime_old_vs_new_comparison.json"
    path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    assert path.exists()


def test_no_decimal_float_cast_outside_boundary():
    """Grep guard: Phase 16 modified modules must not bare-cast Decimal fields."""
    phase16_files = [
        "src/mcc/risk/sizing.py",
        "src/mcc/risk/riskfolio_adapter.py",
        "src/mcc/risk/portfolio.py",
        "src/mcc/performance/analytics.py",
        "src/mcc/performance/quantstats_adapter.py",
        "src/mcc/regime/hmm.py",
        "src/mcc/research/stat_models.py",
    ]
    violations: list[str] = []
    decimal_var_pattern = re.compile(
        r"float\(\s*(raw_frac|capped_frac|risk_dollars|target_vol|current_vol|win_prob|payoff)\s*\)"
    )
    for rel in phase16_files:
        path = Path(rel)
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if decimal_var_pattern.search(line):
                violations.append(f"{path}:{i}: {line.strip()}")
    assert not violations, "Decimal float casts outside boundary:\n" + "\n".join(violations)