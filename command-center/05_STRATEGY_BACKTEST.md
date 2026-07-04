# PHASE 05 — STRATEGY FRAMEWORK · BACKTESTING

**CONTEXT:** Indicators + regime complete. Build the strategy abstraction, its status lifecycle (Principle P1), and both backtesting engines with realistic costs. This is where the validation-first rule becomes structural.

---

## 1. `strategy/base.py`
- `Strategy(ABC)`: typed `params` (pydantic), declared indicator/data dependencies, `warmup`, and methods `generate_signals(context) -> list[SignalEvent]` (pure, no I/O), `describe()` (human-readable rules). A `context` object exposes indicators, regime, internals, and position state at time *t* with **no look-ahead**.
- `SignalEvent` carries: instrument, direction, strength/confidence, intended entry/exit logic, and the strategy id.

## 2. `strategy/lifecycle.py`
- `StrategyStatus` enum `DRAFT → REGISTERED → TESTED → GREEN|YELLOW|RED`. Transitions are guarded functions: e.g., `TESTED` requires a completed walk-forward; `GREEN` requires a passing verdict (Phase 06). No manual jump to `GREEN`. Persist status + timestamps to the `strategies` table.

## 3. `strategy/registry.py`
- Discover strategy classes under `strategies/`; register with id, version, params schema, and current status. Query helpers: `green_strategies()`, `by_id()`. The execution gateway (Phase 10) reads only from here.

## 4. `backtest/costs.py`
- Per-instrument commission + slippage model (config-driven; NQ/ES/CL/GC round-turn costs). A frictionless mode exists only behind an explicit flag and watermarks all outputs `NON-VALID`.

## 5. `backtest/fills.py`
- Realistic fill model for the event-driven engine: next-bar-open or configurable, spread/slippage applied, partial-fill option, session/liquidity awareness (no fills outside traded sessions).

## 6. `backtest/vectorized.py`
- `vectorbt`-based fast scanner for parameter sweeps and idea triage. Explicitly labeled **exploratory** — every combination tested increments a trial counter on the hypothesis (feeds DSR in Phase 06). Outputs are never a basis for GREEN.

## 7. `backtest/event_driven.py`
- Custom event-driven engine consuming the same bus events (or replay) a live strategy would, applying `costs` + `fills`, tracking positions/PnL/drawdown per instrument, and producing a trade blotter + equity curve. This is the engine used for validation and paper trading (shared code path with live = high fidelity).

---

## PHASE 05 ACCEPTANCE GATE
- A worked example strategy (e.g., NQ opening-range breakout) implements `Strategy`, registers as `DRAFT`, and cannot be forced to `GREEN` (transition guard raises).
- Event-driven backtest of the example produces a trade blotter + equity curve; costs applied; no fills outside sessions; no look-ahead (a shuffled-future test doesn't change past trades).
- Vectorized scan runs a small grid and increments the hypothesis trial counter accordingly.
- Frictionless output is watermarked `NON-VALID`.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-VALID (Phase 06) per the dependency graph — no user interaction.
