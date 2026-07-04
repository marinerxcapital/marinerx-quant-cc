# PHASE 13 — TESTS · INTEGRATION · FINAL ACCEPTANCE

**CONTEXT:** Phases 01–12 complete. Harden the whole system with tests, an end-to-end integration run on replay data, documentation, and the master acceptance checklist. The project is not done until every box passes.

---

## 1. Test Suite (`tests/`) — `pytest` + `pytest-asyncio`
Per-module unit tests (carry over each phase's gate as automated tests) plus **cross-module integration tests**:
- `test_bus_supervisor.py` — agents start, heartbeat, restart on crash, killswitch order.
- `test_no_lookahead.py` — indicators, features, and strategy context are point-in-time safe (system-wide).
- `test_validation_discrimination.py` — overfit ⇒ RED, genuine synthetic edge ⇒ GREEN; trial count drives DSR.
- `test_status_gate.py` — status reaches GREEN only via a passing verdict; execution blocks non-GREEN.
- `test_risk_vetoes.py` — LOCKOUT / VaR breach / event window / stale feed each force NO_GO and block execution.
- `test_decision_determinism.py` — identical inputs ⇒ identical decision + reason.
- `test_end_to_end_replay.py` — **the keystone:** stream a cached session via the replay feed through internals → indicators → a GREEN example strategy → decision engine → paper execution → journal → performance, asserting a coherent equity curve, at least one logged decision with reasons, and zero guardrail bypasses.

Target ≥ 70% coverage on core modules (`core, strategy, validation, risk, decision, execution`).

## 2. `README.md` (write in full)
Overview & the three governing principles; architecture diagram; install (`uv sync`, optional `playwright install chromium` for account sync, feed setup); configuration (`config/*.yaml`, `.env`); running (`doctor`, `run`, `tui`, `web`); the research→validation→decision→execution workflow with the worked example; connecting the Tradeify Sync package; data/report locations; **safety posture** (paper-first, live stubbed behind explicit enable; validation-first; risk-first; honest forecasting); limitations and the honest caveat that the system's value is disciplined process and infrastructure, not guaranteed alpha; troubleshooting.

## 3. Quality
`pyproject.toml` with `[tool.pytest.ini_options] asyncio_mode="auto"`; `ruff` clean tree-wide; `mypy --strict src/` clean.

---

## MASTER ACCEPTANCE CHECKLIST (run; report PASS/FAIL per line)
- [ ] `uv sync` succeeds from clean.
- [ ] `python main.py doctor` → all green.
- [ ] `python main.py run` → supervisor + TUI up, all agents live, killswitch works.
- [ ] `python main.py web` → dashboard streams live internals, a full-res heatmap, equity curve, and Trade-or-No-Trade panel via websockets.
- [ ] Example strategy completes DRAFT→REGISTERED→TESTED→verdict; only a passing verdict yields GREEN.
- [ ] Decision engine emits reasoned GO/NO-GO; every veto independently forces NO-GO.
- [ ] Execution refuses non-GREEN strategies and honors PropGuardian LOCKOUT — no override path exists.
- [ ] `test_end_to_end_replay.py` passes end to end.
- [ ] `pytest` green; coverage ≥ 70% on core modules.
- [ ] `ruff` clean; `mypy --strict src/` clean.
- [ ] README lets a new operator reach a running command center and a first paper decision unaided.

On full pass, output a final build report: actual file tree produced, test + coverage summary, agent roster with status, and any deviations from this package with justification.
