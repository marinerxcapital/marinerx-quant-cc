# PHASE 00 — MASTER BRIEF (constitution; read first, retained for every phase)

You are building **MarinerX Quant Command Center (MCC)** — a complete, personal quantitative trading operating system in Python. It is the single hub for the user's trading: data, market internals, live heatmaps, indicators, regime detection, strategy engineering, validation, quant/ML research, risk, a Trade-or-No-Trade decision engine, execution (paper-first), journaling, reporting, a real-time interface, and deployment to Railway.

This message is specification only. Retain it for all later phases. Begin coding at Phase 01 immediately, per the Orchestrator Kickoff charter — no confirmation to the user.

---

## 1. Three Governing Principles (enforce structurally in code)

| # | Principle | Enforcement |
|---|-----------|-------------|
| P1 | **Validation-first** | A `Strategy` has a `status` lifecycle (`DRAFT → REGISTERED → TESTED → GREEN/YELLOW/RED`). The execution gateway raises if `status != GREEN`. No override flag. |
| P2 | **Risk-first** | Risk and PropGuardian vetoes override every signal. The decision engine can be forced to NO-GO by a risk veto regardless of strategy conviction. |
| P3 | **Honest forecasting** | Every predictive model is scored against a naive baseline (persistence/random). Models that don't beat baseline are labeled `NO_SIGNAL` and cannot feed the decision engine. |

## 2. Scope (build all of it)
Indicators · strategy running · analysis · coding/research console · quantitative modeling · futures trading (NQ/ES/CL/GC) · market risk · live market heatmaps · live market internals · Trade-or-No-Trade decision system · historical + live data · account ingestion · backtesting + validation · execution (paper-first, live stubbed) · journaling · performance analytics · reporting · real-time TUI + web interface · **cloud deployment (Railway)**.

## 3. Tech Stack (use exactly these; pin versions)
| Layer | Choice |
|-------|--------|
| Language | Python 3.11+, fully typed; `mypy --strict` clean on `src/` |
| Packaging | `pyproject.toml`, `uv`-compatible, pinned |
| Async core | `asyncio`; in-process pub/sub bus (swappable to Redis/ZeroMQ) |
| Data | `pandas`, `polars`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `lightgbm` |
| Analytical store | `duckdb` over `parquet`; relational state in `sqlite`/`sqlalchemy` |
| Historical feed | `databento` (GLBX.MDP3) |
| Live feed | adapter protocol + concrete adapters: `databento` live, IQFeed (internals: $TICK/$TRIN/$ADD), Tradovate; plus a **replay adapter** for offline dev |
| Backtest | `vectorbt` (scans) + a custom event-driven engine (final validation) |
| Money/time | `Decimal` for money/prices; tz-aware UTC storage; `zoneinfo` |
| Viz/reports | `plotly` (web), `matplotlib` (PDF), report templates |
| Interface | `fastapi`+`uvicorn`+websockets web dashboard (Plotly.js frontend) as the **primary/production interface**; `textual` TUI as a **local-dev-only** secondary surface (a headless cloud host has no interactive terminal to attach) |
| Deployment | **Docker** (multi-stage build) + **Railway** (web service + optional worker service, persistent volumes, env-var secrets) |
| Scheduler | `apscheduler` |
| Resilience | `tenacity` |
| Logging | `structlog` (JSON, rotating) |
| CLI | `typer` |
| Tests/quality | `pytest`, `pytest-asyncio`, `ruff`, `mypy` |

## 4. Canonical Monorepo Tree (authoritative)
```
marinerx-command-center/
├── pyproject.toml
├── config/                      # env yaml configs
├── .env.example
├── Dockerfile                    # multi-stage; Playwright-capable base if AccountSync runs in-container
├── railway.json                  # or nixpacks.toml — Railway build/start config
├── README.md
├── main.py                      # launches supervisor + interface; Typer CLI
├── src/mcc/
│   ├── core/          {config.py, bus.py, base_agent.py, supervisor.py, exceptions.py, clock.py, events.py}
│   ├── storage/       {relational.py, analytical.py, buffers.py}
│   ├── data/
│   │   ├── historical/{databento_client.py, roll.py, catalog.py}
│   │   ├── live/      {feed.py(protocol), databento_live.py, iqfeed.py, tradovate.py, replay.py}
│   │   ├── calendar/  {events.py}
│   │   └── accounts/  {sync_adapter.py}   # integration point for the Tradeify Sync package
│   ├── internals/     {breadth.py}        # TICK/TRIN/ADD/VOLD/VIX, put-call
│   ├── microstructure/{cvd.py, obi.py, volume_profile.py}
│   ├── heatmaps/      {orderbook.py, correlation.py, volatility.py, sector.py}
│   ├── indicators/    {library.py, engine.py}
│   ├── regime/        {hmm.py, volatility_regime.py}
│   ├── strategy/      {base.py, lifecycle.py, registry.py}
│   ├── backtest/      {vectorized.py, event_driven.py, costs.py, fills.py}
│   ├── validation/    {prereg.py, walkforward.py, statistics.py, montecarlo.py, verdict.py}
│   ├── research/      {features.py, forecast_lab.py, stat_models.py, experiments.py}
│   ├── risk/          {sizing.py, var_es.py, portfolio.py, prop_guardian.py, monitor.py}
│   ├── decision/      {engine.py, factors.py, vetoes.py}
│   ├── execution/     {gateway.py, paper_sim.py, live_stub.py, guardrails.py}
│   ├── journal/       {journal.py}
│   ├── performance/   {analytics.py}
│   ├── reports/       {generator.py, templates/}
│   ├── interface/
│   │   ├── web/       {server.py, ws.py, static/}   # primary
│   │   └── tui/       {app.py, panels/}              # local-dev only
│   └── agents/        {registry.py, *_agent.py}   # bus/supervisor wrappers, one per roster entry below
├── strategies/                  # registered hypotheses + strategy classes
├── data/                        # parquet, duckdb, sqlite, downloads (Railway: mounted volume)
├── notebooks/
├── reports_out/
└── tests/
```

## 5. The 15-Agent Roster (runtime AND build-subagent — one consistent set, used both ways)

This single roster of **15 named agents** serves two roles simultaneously: (a) as **runtime services** — each is a supervised async agent with a live dashboard panel, and (b) as **build-subagents** — each name is also the identity of the Grok Build subagent responsible for constructing that module end to end (code + tests). This 1:1 mapping is deliberate: what you watch running is exactly what was built by a named, accountable builder.

| # | Agent | Runtime Responsibility | Owns (`src/mcc/`) | Built In Phase |
|---|-------|------------------------|--------------------|----------------|
| 1 | **Overseer** | Supervisor, kill-switch, health checks, system status header | `core/`, `agents/registry.py` | 01 |
| 2 | **DataOps** | Historical ingestion, live feed adapters, economic calendar | `data/historical/`, `data/live/`, `data/calendar/` | 02 |
| 3 | **AccountSync** | Reads Tradeify Sync's output (SQLite); account state, drawdown headroom | `data/accounts/` | 02 |
| 4 | **MarketPulse** | Market internals, microstructure (CVD/OBI/volume profile), all heatmaps | `internals/`, `microstructure/`, `heatmaps/` | 03 |
| 5 | **IndicatorEngine** | Indicator library + computation engine (batch + incremental) | `indicators/` | 04 |
| 6 | **RegimeMonitor** | Volatility regime + HMM trending/ranging classification | `regime/` | 04 |
| 7 | **StrategyRunner** | Strategy base class, lifecycle/status gate, registry | `strategy/` | 05 |
| 8 | **ValidationEngine** | Backtesting (vectorized + event-driven) + the full validation gauntlet (prereg, walk-forward, DSR/PSR, Monte Carlo, verdict) | `backtest/`, `validation/` | 05, 06 |
| 9 | **ResearchLab** | Feature engineering + honest forecasting (baselines mandatory) + stat models | `research/` | 07 |
| 10 | **RiskCommand** | Sizing (Kelly/vol-target), VaR/ES, portfolio risk, PropGuardian, real-time risk monitor | `risk/` | 08 |
| 11 | **DecisionEngine** | Trade-or-No-Trade: hard vetoes + weighted factor scoring, reasoned GO/NO-GO | `decision/` | 09 |
| 12 | **ExecutionGateway** | Guardrails, paper simulator, live stub (inert by default) | `execution/` | 10 |
| 13 | **TradeJournal** | Fill ingestion, structured trade tagging | `journal/` | 11 |
| 14 | **PerformanceAnalyst** | Equity/Sharpe/drawdown analytics, decision attribution | `performance/` | 11 |
| 15 | **ReportPublisher** | Branded PDF/HTML verdict + weekly reports | `reports/` | 11 |

`interface/` (web dashboard + TUI) and `deploy/` config (Dockerfile, railway.json) are **cross-cutting deliverables** owned directly by the Build Manager with subagent support as needed (Phases 12 and 14) — not a 16th named agent, since they serve every agent rather than owning a market/trading domain of their own.

`BaseAgent` provides: name, status (idle/working/error), heartbeat, current_task, ring-buffer log, metrics dict, `on_event`, `emit`. Supervisor restarts dead agents and owns a global kill-switch.

## 6. Coding Standards
Full type hints; `Decimal` money; tz-aware UTC; concise docstrings; custom exception hierarchy in `core/exceptions.py`; no side effects on import; never log secrets/tokens/full payloads; deterministic hashing for dedup; all live data flows through the bus so the interface mirrors state in real time.

## 7. Global Acceptance Gates
`uv sync` clean · `python main.py doctor` all-green · supervisor launches all 15 agents · web interface renders live panels · example strategy runs full lifecycle to a verdict · decision engine emits reasoned GO/NO-GO · execution refuses non-GREEN strategies · `pytest` green · `ruff` + `mypy --strict src/` clean · **Railway deployment gate (Phase 14) passes: container builds, health check responds, dashboard reachable at the public domain.**

## 8. Build Order
01 Core (Overseer) → 02 Data (DataOps, AccountSync) → 03 Internals/Heatmaps (MarketPulse) → 04 Indicators/Regime (IndicatorEngine, RegimeMonitor) → 05 Strategy/Backtest (StrategyRunner, ValidationEngine-part-1) → 06 Validation (ValidationEngine-part-2) → 07 Research (ResearchLab) → 08 Risk (RiskCommand) → 09 Decision (DecisionEngine) → 10 Execution (ExecutionGateway) → 11 Journal/Perf/Reports (TradeJournal, PerformanceAnalyst, ReportPublisher) → 12 Interface (web-primary + TUI-dev) → 13 Tests/Acceptance (local, full system) → 14 Railway Deployment (final, after 13 passes locally).

Build Manager: internalize this constitution, then dispatch the Overseer subagent on Phase 01 immediately. No confirmation to the user — proceed autonomously per the Orchestrator Kickoff charter.
