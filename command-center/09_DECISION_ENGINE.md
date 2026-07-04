# PHASE 09 — TRADE-OR-NO-TRADE DECISION ENGINE

**CONTEXT:** Internals/heatmaps, indicators/regime, strategy, validation, and risk are all live on the bus. Build the decision engine — the system that turns everything into a single, explainable **GO / NO-GO** per instrument, with hard vetoes that cannot be overridden by conviction.

---

## 1. `decision/vetoes.py` (hard layer — evaluated first)
A GO is impossible if **any** veto fires; each returns a reason:
- **Validation veto:** no `GREEN` strategy currently signaling this instrument.
- **Risk veto:** PropGuardian `LOCKOUT`, VaR/ES over limit, or per-instrument cap reached.
- **Event veto:** inside a configured blackout window around high-impact events (from the calendar) unless the signaling strategy is explicitly event-designed.
- **Data-health veto:** stale/again-degraded feed, missing internals, or `NO_BOOK` when the strategy requires book data.
- **Session veto:** outside the instrument's tradeable session.

## 2. `decision/factors.py` (soft layer — scored only if no veto)
Weighted, normalized factors (weights in config,每 factor emits its contribution + explanation):
- Strategy signal strength/confidence (from `GREEN` strategies only).
- Regime alignment (HMM state + vol regime vs. the strategy's designed regime).
- Market internals alignment (breadth regime, $TICK/$TRIN extremes for/against the trade).
- Microstructure confirmation (CVD direction, OBI, proximity to POC/value area).
- Forecast-lab `SIGNAL` models (never `NO_SIGNAL`) as an optional confirming input.
- Risk headroom quality (size available under current PropGuardian/vol-target state).

## 3. `decision/engine.py`
- `DecisionEngine` agent: on each relevant bus update, run vetoes → if clear, compute the weighted factor score → map to a `Decision` (`GO`/`NO_GO`/`STAND_ASIDE`) with a confidence band and a **full reason string** (which vetoes passed, each factor's contribution, recommended size from the risk engine). Publish `DecisionEvent`; never auto-executes — it advises execution (Phase 10) and lights the interface's Trade-or-No-Trade panel.
- Fully deterministic and logged: given the same inputs, the same decision + identical reasoning. Every decision is persisted for later performance attribution (was GO/NO-GO right?).

---

## PHASE 09 ACCEPTANCE GATE
- With no `GREEN` strategy, the engine always returns `NO_GO` with the validation-veto reason.
- Each veto independently forces `NO_GO` on a constructed scenario (LOCKOUT, VaR breach, event window, stale feed, closed session).
- With vetoes clear, factor weights change the score predictably; the reason string enumerates every factor's contribution.
- Determinism test: identical inputs → identical decision + reason.
- Decisions persist and are queryable for attribution.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-EXEC (Phase 10) per the dependency graph — no user interaction.
