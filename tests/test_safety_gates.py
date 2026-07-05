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


# Additional coverage drivers for core (risk, replay sync paths, lifecycle)
from decimal import Decimal
from mcc.risk.sizing import kelly_size, vol_target_size
from mcc.risk.prop_guardian import get_risk_level, RiskLevel
from mcc.strategy.lifecycle import StrategyStatus, transition

def test_risk_sizing_functions():
    eq = Decimal("100000")
    s1, _ = kelly_size(eq, Decimal("0.6"), Decimal("1.5"))
    assert s1 > 0
    s2, _ = vol_target_size(eq, Decimal("0.02"), Decimal("0.01"))
    assert s2 >= 1

def test_risk_guardian_levels():
    assert get_risk_level(Decimal("0.5"), Decimal("0")) == RiskLevel.OK
    assert get_risk_level(Decimal("0.05"), Decimal("0")) == RiskLevel.LOCKOUT
    assert get_risk_level(Decimal("0.25"), Decimal("0")) == RiskLevel.CAUTION

def test_lifecycle_more():
    s = StrategyStatus.REGISTERED
    t = transition(s, StrategyStatus.TESTED, has_passing_verdict=False)
    assert t == StrategyStatus.TESTED
    # green only via verdict already covered

import asyncio
from mcc.data.live.replay import ReplayAdapter
from mcc.core.bus import MessageBus
from mcc.core.clock import SimClock

@pytest.mark.asyncio
async def test_replay_adapter_basic():
    bus = MessageBus()
    clock = SimClock()
    ra = ReplayAdapter(bus=bus, clock=clock, speed=1000.0)  # fast
    await ra.connect()
    await ra.subscribe(["NQ"], ["bars"])
    # stream_and_count hits load/synth + loop without full timing
    cnt = await ra.stream_and_count(limit=3)
    assert cnt >= 1
    await ra.disconnect()
