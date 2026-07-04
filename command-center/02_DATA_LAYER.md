# PHASE 02 — DATA LAYER (historical · live · calendar · accounts)

**CONTEXT:** Core infra (bus, agents, supervisor, storage, clock, events) complete. Build every data source. All feeds publish to the bus and/or persist to the parquet/duckdb catalog. Live feeds are abstracted behind one protocol with swappable adapters + an offline replay adapter so the whole system is developable without a live subscription.

---

## 1. `data/historical/databento_client.py`
- Authenticated Databento client (key from `.env`); pull GLBX.MDP3 1-min (and configurable) bars for NQ/ES/CL/GC; graceful degradation to cached parquet when offline.
- `data/historical/roll.py`: volume/open-interest based continuous-contract stitching; document the roll rule; tag roll dates.
- `data/historical/catalog.py`: parquet catalog (partitioned by symbol/date); integrity checks (gaps, duplicate timestamps, session coverage); register datasets with DuckDB.

## 2. `data/live/feed.py` — the abstraction
- `LiveFeed(Protocol)`: `async connect()`, `async subscribe(symbols, channels)` where channels ∈ {`trades`,`quotes`,`bars`,`book`,`internals`}, `async stream() -> AsyncIterator[Event]`, `async disconnect()`. Normalizes every adapter's payload into core `TickEvent`/`BarEvent`/`InternalsEvent`/book updates.
- A `FeedAgent` wraps the active feed, publishes to the bus, and writes to ring buffers + rolling parquet.

## 3. Live adapters (implement all; each behind the protocol)
- `databento_live.py` — Databento live for trades/quotes/bars.
- `iqfeed.py` — IQFeed adapter; **primary source for market internals** ($TICK, $TRIN, $ADD, $VOLD, $VIX) and Level 1/2. Clearly document required IQFeed subscription; degrade cleanly if absent.
- `tradovate.py` — Tradovate market-data adapter (if the user's data entitlement allows), read-only for quotes/fills.
- `replay.py` — **replay adapter**: streams historical parquet through the bus at configurable speed using `SimClock`, so internals/heatmaps/indicators/decision engine are fully testable offline. This is the default in `dev`.

## 4. `data/calendar/events.py`
- Economic calendar ingestion (EIA Wed 10:30 ET, FOMC, CPI, NFP, etc.); expose `next_event(instrument, now)` and `in_event_window(now, pre_min, post_min)`; publish `InternalsEvent`-adjacent `EventProximity` state consumed by the decision engine's event veto.

## 5. `data/accounts/sync_adapter.py`
- Integration point for the **Tradeify Sync Engine** (separate package). Consume its normalized `AccountStateEvent`/`TradeNewEvent`/`DrawdownUpdateEvent` (via the bus endpoint) and republish onto the MCC bus for `PropGuardian`, `TradeJournal`, and the interface. If the sync engine isn't running, degrade to last-known state from sqlite and flag staleness.

---

## PHASE 02 ACCEPTANCE GATE
- Historical: pull (or load cached) NQ 1-min bars, stitch a continuous contract, register with DuckDB; a SQL query returns expected row counts; integrity report lists any gaps.
- Live abstraction: `replay.py` streams a day of cached bars through the bus at 60× using `SimClock`; a subscriber counts the expected events; switching the configured adapter requires no consumer changes.
- Calendar: `next_event("CL", t)` returns the upcoming EIA release; `in_event_window` correct around 10:30 ET.
- Account adapter: fed a sample `DrawdownUpdateEvent`, it republishes on the MCC bus; absent the engine, it reports stale last-known state.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-MARKET (Phase 03) per the dependency graph — no user interaction.
