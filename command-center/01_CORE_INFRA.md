# PHASE 01 — CORE INFRASTRUCTURE

**CONTEXT:** Master Brief (Phase 00) retained. Build the backbone every module plugs into. Deliver complete, runnable code; at phase end the supervisor must start, run a heartbeat, and route a test event across the bus.

---

## 1. `core/exceptions.py`
Hierarchy: `MCCError` → `ConfigError`, `BusError`, `AgentError`, `DataError`, `FeedError`, `ValidationError`, `RiskVeto`, `ExecutionBlocked`, `IntegrityError`.

## 2. `core/config.py`
- `pydantic-settings` models mirroring `config/*.yaml` + `.env` secrets. Sections: `runtime`, `data`, `feeds`, `instruments` (NQ 0.25/5.00, ES 0.25/12.50, CL 0.01/10.00, GC 0.10/10.00), `risk`, `decision`, `interface`, `logging`.
- `Settings.load(env="dev")`, validation, cached `get_settings()`.

## 3. `core/clock.py`
- `Clock` protocol with `RealClock` (wall time, UTC) and `SimClock` (for replay/backtests). Everything time-dependent takes a `Clock` — never call `datetime.now()` directly. CME session helpers (RTH/ETH in `America/New_York`, DST-aware).

## 4. `core/events.py`
- Typed event dataclasses (frozen), each with `topic`, `ts_utc`, `source`, `payload`. Define at least: `BarEvent`, `TickEvent`, `InternalsEvent`, `HeatmapEvent`, `IndicatorEvent`, `RegimeEvent`, `SignalEvent`, `RiskEvent`, `DecisionEvent`, `OrderEvent`, `FillEvent`, `AccountStateEvent`, `AgentStatusEvent`, `LogEvent`.
- A `Topic` enum for the pub/sub namespace.

## 5. `core/bus.py`
- `MessageBus`: async in-process pub/sub over `asyncio.Queue` per subscriber. `subscribe(topic|topics) -> AsyncIterator[Event]`, `publish(event)`, wildcard subscription, backpressure policy (bounded queues, drop-oldest for high-rate live topics with a dropped-count metric). Designed so the transport can be swapped for Redis/ZeroMQ behind the same interface.

## 6. `core/base_agent.py`
- `BaseAgent(ABC)`: `name`, `status`, `heartbeat_ts`, `current_task`, `log` ring-buffer (last N), `metrics: dict`. Lifecycle `async start/stop/run`; helpers `emit(event)`, `set_status`, `log_line`. Publishes an `AgentStatusEvent` on every state change so the interface reflects it live. Subclasses implement `async work()`.

## 7. `core/supervisor.py`
- `Supervisor`: registers agents, starts them as supervised asyncio tasks, monitors heartbeats, restarts crashed agents (backoff, max restarts), exposes `kill_switch()` that halts execution-capable agents first. Aggregates a `SystemStatus` snapshot for the interface.

## 8. `storage/relational.py`
- SQLAlchemy 2.x engine/session + `session_scope()`; tables for `strategies`, `hypotheses`, `verdicts`, `trades`, `journal_entries`, `sync_runs`, `experiments`. `init_db()`.

## 9. `storage/analytical.py`
- DuckDB connection over the parquet catalog; helpers to register/query parquet datasets (bars, internals) with SQL; write helpers for research outputs.

## 10. `storage/buffers.py`
- Fixed-size, thread/async-safe in-memory ring buffers for live series (bars, ticks, internals, order book) that feed indicators/heatmaps and the interface without hitting disk.

---

## PHASE 01 ACCEPTANCE GATE
- `python -c "from mcc.core.supervisor import Supervisor"` imports clean.
- A demo script starts the supervisor with a dummy agent that emits a `LogEvent` every second; a second subscriber receives it via the bus; kill-switch stops cleanly.
- `init_db()` creates all relational tables; DuckDB opens over an empty catalog.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-DATA (Phase 02) per the dependency graph — no user interaction.
