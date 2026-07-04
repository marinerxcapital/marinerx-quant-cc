# MarinerX Quant Command Center — SuperGrok Build Package

A phased, dependency-ordered build package for a complete personal quantitative trading **command center** in Python: historical + live data, market internals, live heatmaps, indicators, regime detection, strategy engineering, a validation gauntlet, quant/ML research, risk management, a **Trade-or-No-Trade decision engine**, execution (paper-first), journaling, reporting, a real-time web dashboard (+ local-dev TUI), and **Railway cloud deployment**.

Instruments in scope: **NQ, ES, CL, GC** (extensible). **15 named agents**, identical set for runtime services and build-subagents.

---

## How To Use — AUTONOMOUS MODE (Grok Build, SuperGrok Heavy)

This package runs as a **Grok Build `/goal` objective** — see `../START_HERE.md` → "Execution Environment" for the verified Windows PowerShell install/launch commands.

1. **User action (once, total):** install Grok Build, authenticate with SuperGrok Heavy, extract this package, run the objective in `../GROK_KICKOFF_PROMPT.md`.
2. Grok Build acts as **Build Manager**, dispatching each of the 15 subagents (one per Master Brief §5 roster entry) per the dependency graph below, each in its own git worktree, self-verifying every phase's Acceptance Gate with captured evidence, and looping on its own failures.
3. **No further user involvement** beyond occasionally noticing if a `/goal` run stalls (a known beta-maturity limitation of parallel subagent coordination — see `00B_PRE_FLIGHT_ADDENDUM.md` §4) and issuing a bare "continue." `PROGRESS.md` and the git history make any such restart require zero re-explanation.
4. The user's next real interaction is receiving the **Final Build Report**, emitted only after Phase 14's Railway deployment gate passes (which itself requires Phase 13's local Master Acceptance Checklist to be fully green first).
5. The separately delivered **Tradeify Sync package** plugs into Phase 02 as the AccountSync module — attach it alongside this package.

---

## Architecture At A Glance

```
                    ┌────────── WEB DASHBOARD (Phase 12, primary) ──────────┐
                    │      FastAPI + websockets + Plotly.js  (Railway)      │
                    │         [local-dev-only TUI also available]           │
                    └───────────────▲──────────────────────▲────────────────┘
                                    │ live status/panels    │
    ┌───────────────────────── EVENT BUS + OVERSEER (Phase 01) ─────────────────────────┐
    │                                                                                    │
DataOps/AccountSync(02)   MarketPulse(03)   IndicatorEngine/RegimeMonitor(04)  StrategyRunner(05)
hist/live/cal/accounts    TICK/TRIN/ADD     library+engine / HMM+vol regime    lifecycle+registry
                           CVD/OBI/POC
                           heatmaps                                                       │
    └──────────────► ValidationEngine(05,06) ─► ResearchLab(07) ─► RiskCommand(08) ──────┘
                      backtest+WFO+DSR+verdict    features+forecast+stats      sizing/VaR/ES/
                                                                                PropGuardian
                                        │
                          DecisionEngine(09): GO/NO-GO with reasons
                          (hard vetoes: validation, risk, event, data-health, session)
                                        │
                          ExecutionGateway(10): paper-first, live stubbed
                                        │
              TradeJournal(11) · PerformanceAnalyst(11) · ReportPublisher(11)
                                        │
                          Phase 14: Docker + Railway deployment
```

---

## Build Order & Dependencies (15 agents, 14 work orders)

| Phase | Module | Agent(s) | Depends on |
|------|--------|----------|-----------|
| 00 | Master Brief (constitution) | — | — |
| 00B | Pre-Flight Addendum | — | 00 |
| 01 | Core infrastructure | Overseer | 00 |
| 02 | Data layer (historical/live/calendar/accounts) | DataOps, AccountSync | 01 |
| 03 | Market internals · microstructure · heatmaps | MarketPulse | 01,02 |
| 04 | Indicator & signal engine · regime | IndicatorEngine, RegimeMonitor | 01,02 |
| 05 | Strategy framework · backtesting | StrategyRunner, ValidationEngine (part 1) | 01,02,04 |
| 06 | Validation gauntlet | ValidationEngine (part 2) | 05 |
| 07 | Quant modeling · research lab | ResearchLab | 02,04,06 |
| 08 | Risk engine · PropGuardian · monitor | RiskCommand | 02,03 |
| 09 | Trade-or-No-Trade decision engine | DecisionEngine | 03,04,05,06,08 |
| 10 | Execution gateway (paper-first) | ExecutionGateway | 06,08,09 |
| 11 | Journal · performance · reporting | TradeJournal, PerformanceAnalyst, ReportPublisher | 02,08,10 |
| 12 | Command center interface (web-primary + TUI-dev) | cross-cutting | all above |
| 13 | Tests · integration · final acceptance (local) | cross-cutting | all |
| 14 | Railway deployment (final) | cross-cutting | 13 |

---

## Global Success Definition

From a clean checkout: `uv sync` succeeds; `python main.py doctor` all-green; the Overseer launches all 15 agents and the web interface renders live panels; a worked example strategy flows registration → backtest → walk-forward → verdict; the decision engine emits a reasoned GO/NO-GO; execution refuses any non-GREEN strategy; `pytest` green; `ruff` + `mypy --strict src/` clean; **Docker image builds and the Railway health check passes.**

---

## Files

`00_ORCHESTRATOR_KICKOFF.md` **(the objective Grok Build reads first)** · `00B_PRE_FLIGHT_ADDENDUM.md` · `INDEX.md` · `00_MASTER_BRIEF.md` · `01_CORE_INFRA.md` · `02_DATA_LAYER.md` · `03_INTERNALS_HEATMAPS.md` · `04_INDICATORS_REGIME.md` · `05_STRATEGY_BACKTEST.md` · `06_VALIDATION_GAUNTLET.md` · `07_RESEARCH_LAB.md` · `08_RISK_ENGINE.md` · `09_DECISION_ENGINE.md` · `10_EXECUTION.md` · `11_JOURNAL_PERF_REPORTS.md` · `12_INTERFACE.md` · `13_TESTS_ACCEPTANCE.md` · `14_RAILWAY_DEPLOYMENT.md`
