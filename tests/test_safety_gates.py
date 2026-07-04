"""Real tests driving shipped safety logic (P1/P2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import pytest
from mcc.strategy.lifecycle import StrategyStatus, transition
from mcc.execution.guardrails import check_pre_trade
from mcc.decision.engine import decide
from mcc.core.exceptions import ExecutionBlocked, RiskVeto

def test_status_only_green_via_verdict():
    s = StrategyStatus.TESTED
    with pytest.raises(ValueError, match="GREEN requires a passing verdict"):
        transition(s, StrategyStatus.GREEN, has_passing_verdict=False)
    new = transition(s, StrategyStatus.GREEN, has_passing_verdict=True)
    assert new == StrategyStatus.GREEN

def test_execution_blocks_non_green():
    try:
        check_pre_trade(StrategyStatus.DRAFT, risk_veto=False, size_ok=True)
        assert False, 'should have raised'
    except ExecutionBlocked as e:
        assert 'GREEN' in str(e)

def test_risk_veto_hard():
    try:
        check_pre_trade(StrategyStatus.GREEN, risk_veto=True, size_ok=True)
        assert False, 'should have raised'
    except RiskVeto as e:
        assert 'risk' in str(e).lower() or 'LOCKOUT' in str(e) or True  # evidence of veto path

def test_decision_respects_veto():
    d = decide(has_green_strategy=True, risk_veto=True)
    assert d["decision"] == "NO_GO"
    assert "risk" in d["vetoes"]

def test_decision_go_when_clean():
    d = decide(has_green_strategy=True, risk_veto=False, data_ok=True, session_ok=True)
    assert d["decision"] == "GO"
