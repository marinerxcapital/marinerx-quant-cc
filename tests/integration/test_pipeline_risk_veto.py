"""Integration: RiskCommand veto must flow through the live pipeline spine.

test_safety_gates.py proves decide()/check_pre_trade() in isolation; this module
drives BAR/DECISION events through bootstrap + subscribed agents.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from mcc.core.events import DecisionEvent, Event, Topic
from mcc.runtime.bootstrap import create_supervisor


def _risk_lockout_event() -> Event:
    return Event(
        Topic.LOG,
        datetime.now(timezone.utc),
        "RiskCommand",
        {
            "risk_state": {
                "risk_level": "LOCKOUT",
                "veto": True,
                "veto_reason": "PropGuardian LOCKOUT: test",
            },
            "veto": True,
        },
    )


@pytest.mark.asyncio
async def test_pipeline_lockout_forces_no_go():
    sup = create_supervisor(replay=True)
    decisions: list[Event] = []
    fills: list[Event] = []

    async def collector():
        async for ev in sup.bus.subscribe(topics=[Topic.DECISION, Topic.FILL]):
            if ev.topic == Topic.DECISION:
                decisions.append(ev)
            if ev.topic == Topic.FILL:
                fills.append(ev)
            if decisions:
                break

    coll = asyncio.create_task(collector())
    await sup.start_all()
    await asyncio.sleep(0.3)

    await sup.bus.publish(_risk_lockout_event())
    await asyncio.sleep(0.2)

    await sup.bus.publish(
        Event(Topic.BAR, datetime.now(timezone.utc), "replay", {"symbol": "NQ"})
    )
    await asyncio.sleep(1.0)
    coll.cancel()
    await sup.kill_switch()

    assert len(decisions) >= 1
    assert decisions[0].payload.get("decision") == "NO_GO"
    assert "risk" in decisions[0].payload.get("reason", "")
    assert len(fills) == 0


@pytest.mark.asyncio
async def test_pipeline_ok_state_produces_go():
    sup = create_supervisor(replay=True)
    decisions: list[Event] = []
    fills: list[Event] = []

    async def collector():
        async for ev in sup.bus.subscribe(topics=[Topic.DECISION, Topic.FILL]):
            if ev.topic == Topic.DECISION:
                decisions.append(ev)
            if ev.topic == Topic.FILL:
                fills.append(ev)
            if len(decisions) >= 1 and len(fills) >= 1:
                break

    coll = asyncio.create_task(collector())
    await sup.start_all()
    await asyncio.sleep(0.3)

    await sup.bus.publish(
        Event(Topic.BAR, datetime.now(timezone.utc), "replay", {"symbol": "NQ"})
    )
    await asyncio.sleep(1.0)
    coll.cancel()
    await sup.kill_switch()

    assert len(decisions) >= 1
    assert decisions[0].payload.get("decision") == "GO"
    assert len(fills) >= 1


@pytest.mark.asyncio
async def test_execution_blocks_go_when_risk_veto_active():
    """ExecutionGateway must honor live veto state even if a GO decision is injected."""
    sup = create_supervisor(replay=True)
    blocked: list[Event] = []

    async def block_collector():
        async for ev in sup.bus.subscribe(Topic.LOG):
            if "blocked" in ev.payload:
                blocked.append(ev)
                break

    coll = asyncio.create_task(block_collector())
    await sup.start_all()
    await asyncio.sleep(0.3)

    await sup.bus.publish(_risk_lockout_event())
    await asyncio.sleep(0.2)

    go_dec = DecisionEvent(
        ts_utc=datetime.now(timezone.utc),
        source="test",
        symbol="NQ",
        decision="GO",
        reason="injected GO under veto",
        size=1,
    )
    await sup.bus.publish(go_dec)
    await asyncio.sleep(0.5)
    coll.cancel()
    await sup.kill_switch()

    assert len(blocked) >= 1
    assert "RiskVeto" in blocked[0].payload.get("blocked", "") or "risk" in blocked[0].payload.get("blocked", "").lower()