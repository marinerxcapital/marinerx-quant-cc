# PHASE 10 — EXECUTION GATEWAY (paper-first, live stubbed)

**CONTEXT:** Decision engine emits reasoned GO/NO-GO. Build execution. It ships pointed at an internal paper simulator; the live adapter is stubbed behind a manual config change and explicit warnings. Principles P1/P2 are enforced at the gateway.

---

## 1. `execution/guardrails.py`
- Pre-trade checks executed on every order, each able to reject with a reason: strategy `status == GREEN` (else `ExecutionBlocked`); PropGuardian not `LOCKOUT`; order size ≤ risk-engine recommendation and ≤ caps; instrument session open; not inside an event blackout unless permitted; duplicate/rapid-fire order throttle. No override flag exists.

## 2. `execution/paper_sim.py`
- Internal paper-trading simulator sharing the Phase-05 fill model: accepts orders, simulates realistic fills against live/replay prices, tracks positions/PnL/drawdown, and emits `FillEvent`s onto the bus (so journal, performance, risk, and interface all update as in live). Deterministic under `SimClock`.

## 3. `execution/live_stub.py`
- Live broker adapter interface (Tradovate-shaped) fully defined but **inert by default**: methods raise `ExecutionBlocked("live disabled")` unless `runtime.live_enabled` is explicitly true AND a confirmation token is set. Loud warnings on any attempt. No credentials required to build; document exactly what enabling live would require.

## 4. `execution/gateway.py`
- `ExecutionGateway` agent: the only component that places orders. Flow: receive a `GO` `DecisionEvent` → run `guardrails` → size from risk engine → route to `paper_sim` (default) or `live_stub` → log the full decision→order→fill chain. Rejections are logged with reasons and surfaced to the interface. Emits nothing to a broker unless every guardrail passes.

---

## PHASE 10 ACCEPTANCE GATE
- Submitting an order for a non-`GREEN` strategy raises `ExecutionBlocked` (proves P1 at the gateway).
- PropGuardian `LOCKOUT` blocks all new orders (proves P2).
- Paper sim fills a permitted order, emits a `FillEvent`, and updates positions/PnL; journal + performance + risk react.
- Live stub refuses to act without explicit enable + token; default build never contacts a broker.
- Full decision→order→fill chain is logged and reconstructable.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-RECORDS (Phase 11) per the dependency graph — no user interaction.
