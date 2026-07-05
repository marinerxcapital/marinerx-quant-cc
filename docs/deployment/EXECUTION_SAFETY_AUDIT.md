# Execution Safety Audit

Audit of safety guardrails implemented in the deployment migration. **Default posture: no live execution in cloud.**

**Audit date:** Migration implementation (2026-07)  
**Scope:** Config, lifecycle, decision vetoes, execution guardrails, Tradeify policy

## Executive summary

| Control | Status | Default |
|---------|--------|---------|
| `ENABLE_LIVE_EXECUTION` | Implemented | `false` |
| Strategy lifecycle (GREEN gate) | Implemented | Verdict-required |
| Decision hard vetoes | Implemented | `NO_GO` on any veto |
| Execution guardrails | Implemented | Blocks non-GREEN / risk / size |
| Tradeify cloud block | Implemented | Hard error |
| Live keys in Docker | Not required | Replay adapter default |
| Production `ENABLE_LIVE_EXECUTION` in render.yaml | Explicitly `false` | ✓ |

**Verdict:** Safe to deploy to Render with `ENABLE_LIVE_EXECUTION=false`. Live trading requires multiple deliberate gates beyond flipping one env var.

---

## 1. Configuration gate

**File:** `src/mcc/core/config.py`

```python
enable_live_execution: bool = Field(default=False, alias="ENABLE_LIVE_EXECUTION")
```

- Parses only `1`, `true`, `yes`, `on` as true; everything else → false
- Exposed in `/health` as `live_execution_enabled` for observability
- `render.yaml` sets `"false"` on web and worker

**Tests:** `tests/deployment/test_config.py::test_enable_live_execution_defaults_false`

**Gap:** `ENABLE_LIVE_EXECUTION` is config-only today — execution spine does not yet branch on it for broker connectivity. Flag is preparatory + observability. Replay mode remains default regardless.

---

## 2. Strategy lifecycle (P1)

**File:** `src/mcc/strategy/lifecycle.py`

- Status enum: `DRAFT → REGISTERED → TESTED → GREEN/YELLOW/RED`
- **GREEN requires `has_passing_verdict=True`** — no override path
- Illegal transitions raise `ValueError`

**Tests:** `tests/test_safety_gates.py::test_status_only_green_via_verdict`

---

## 3. Decision engine vetoes

**File:** `src/mcc/decision/engine.py`

`decide()` applies hard vetoes before any GO:

| Veto key | Condition |
|----------|-----------|
| `validation` | `has_green_strategy=False` |
| `risk` | `risk_veto=True` |
| `data-health` | `data_ok=False` |
| `session` | `session_ok=False` |

Any veto → `{"decision": "NO_GO", "vetoes": [...]}`

**Pipeline:** `DecisionEngineAgent` in `src/mcc/agents/pipeline.py` calls `decide()` on verdict events.

**Tests:** `tests/test_safety_gates.py::test_decision_respects_veto`, `test_decision_go_when_clean`

---

## 4. Execution guardrails (P1/P2)

**File:** `src/mcc/execution/guardrails.py`

`check_pre_trade()` raises before any fill:

| Check | Exception |
|-------|-----------|
| `strategy_status != GREEN` | `ExecutionBlocked` |
| `risk_veto=True` | `RiskVeto` |
| `size_ok=False` | `ExecutionBlocked` |

**Pipeline:** `ExecutionGatewayAgent` calls `check_pre_trade()` only when decision is `GO`; catches `ExecutionBlocked`/`RiskVeto` and logs block.

**Tests:** `tests/test_safety_gates.py::test_execution_blocks_non_green`, `test_risk_veto_hard`

---

## 5. Risk layer

**Files:** `src/mcc/risk/prop_guardian.py`, `src/mcc/risk/sizing.py`

- `get_risk_level()` → `LOCKOUT` at 5% drawdown threshold
- Sizing functions enforce caps via `kelly_size` / `vol_target_size`

**Resolved (CRITICAL PATCH 01, 2026-07-05):** `RiskCommandAgent` publishes veto state on the bus via `RiskMonitor`. `DecisionEngineAgent` and `ExecutionGatewayAgent` subscribe to `RiskCommand` LOG events and pass the live `risk_veto` value into `decide()` and `check_pre_trade()`.

**Integration test:** `tests/integration/test_pipeline_risk_veto.py` — proves LOCKOUT forces `NO_GO` through the actual pipeline and that `ExecutionGatewayAgent` blocks injected GO decisions when veto is active.

---

## 6. Tradeify local-only

**File:** `src/mcc/core/tradeify_guard.py`

Blocks browser automation in cloud/production → `CloudTradeifyAutomationBlockedError`.

See `TRADEIFY_LOCAL_ONLY_POLICY.md`.

---

## 7. Supervisor / kill switch

**File:** `src/mcc/core/supervisor.py`, `main.py`

- Worker heartbeats record `kill_active` from supervisor snapshot
- Shutdown path calls `supervisor.kill_switch()` on SIGTERM

---

## 8. Exception taxonomy

**File:** `src/mcc/core/exceptions.py`

| Exception | Meaning |
|-----------|---------|
| `ExecutionBlocked` | Pre-trade gate failed |
| `RiskVeto` | Risk layer hard stop |
| `CloudTradeifyAutomationBlockedError` | Tradeify automation in cloud |
| `ConfigError` | Missing production config |

---

## 9. Deployment safety checklist

Before any production promotion:

- [ ] `ENABLE_LIVE_EXECUTION=false` on Render web + worker
- [ ] `/health` shows `live_execution_enabled: false`
- [ ] `python main.py doctor` passes
- [ ] `python -m pytest tests/test_safety_gates.py tests/deployment/ -q` passes
- [ ] No Playwright in Docker image
- [ ] Tradeify specs remain docs-only (`tradeify-sync/`)

## 10. Enabling live execution (future — not migration scope)

Requires **all** of:

1. Explicit business approval
2. `ENABLE_LIVE_EXECUTION=true` only after code paths honor the flag
3. Broker credentials via secure secret store (not in repo)
4. Strategy in `GREEN` with passing verdict
5. Risk limits configured and tested
6. Separate staging soak period

**Do not enable on initial Render migration.**