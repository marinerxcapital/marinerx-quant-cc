# PHASE 12 — COMMAND CENTER INTERFACE (TUI + Web)

**CONTEXT:** All backend agents publish state on the bus. Build the "sharp interface" — a real-time mission control that renders every agent and every live data view, plus a coding/research console. Both surfaces subscribe to the same bus, so they always mirror true system state.

---

## 1. `interface/tui/app.py` + `interface/tui/panels/`
- `textual` full-screen app. Layout: header (system status, day/week P&L, active-account `drawdown_headroom`, global kill-switch), an **agent grid** (one panel per agent: status light, current task, last log lines, key metric), and focus panels for: live internals ($TICK/$TRIN/$ADD/$VIX with sparklines), a compact heatmap (downsampled), regime snapshot, the **Trade-or-No-Trade panel** (current GO/NO-GO per instrument with the reason string), open positions/PnL, and recent decisions/fills.
- Command bar: `register <hyp>`, `test <id>`, `verdict <id>`, `backtest <id>`, `decide <instrument>`, `journal add`, `report weekly`, `killswitch`. Semantic colors for GREEN/YELLOW/RED and risk states; errors impossible to miss.

## 2. `interface/web/server.py` + `ws.py` + `static/`
- `fastapi` + `uvicorn`; a websocket (`ws.py`) bridges bus events to the browser. Single-page dashboard (`static/`, Plotly.js) rendering the **full-resolution heatmaps** (order book depth, correlation, volatility — all via one Plotly component using the Phase-03 common frame schema), live internals charts, equity curve, agent grid, risk gauges, and the Trade-or-No-Trade panel. Read-only views by default; control actions (e.g., killswitch) require an explicit confirm.
- Throttle high-rate topics to a sane UI refresh; show a dropped-frames indicator if backpressure kicks in.

## 3. Coding / research console
- A console surface (TUI tab + web page) to run research snippets against the analytical store and forecast lab, launch experiments, and view results — without leaving the hub. Sandboxed to the project's data/APIs.

## 4. `main.py`
- Typer CLI + launcher: `run` (start supervisor + chosen interface), `tui`, `web`, `doctor`, plus the strategy/validation/report commands. `doctor` validates config, `.env`, data catalog, feed connectivity (or replay availability), DB, and that all agents can start.

---

## PHASE 12 ACCEPTANCE GATE
- `python main.py run` starts the supervisor and TUI; the agent grid shows all agents live; killswitch halts execution-capable agents first.
- `python main.py web` serves the dashboard; a replay session drives live-updating internals, at least one full-resolution heatmap, equity curve, and the Trade-or-No-Trade panel over websockets.
- The Trade-or-No-Trade panel shows the current decision + full reason string and updates as inputs change.
- `doctor` reports all-green on a correctly configured environment.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-QA final integration (Phase 13) per the dependency graph — no user interaction.
