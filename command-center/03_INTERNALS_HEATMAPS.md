# PHASE 03 — MARKET INTERNALS · MICROSTRUCTURE · LIVE HEATMAPS

**CONTEXT:** Data layer complete (historical + live feeds via protocol, calendar, account sync). Now build the real-time market-state layer that feeds indicators, the decision engine, and the interface. Everything here consumes bus events (works identically on live or replay) and republishes computed state.

---

## 1. `internals/breadth.py` — market internals
- Consume internals channel ($TICK, $TRIN, $ADD, $VOLD, $VIX) plus put/call where available.
- Compute and publish rolling `InternalsEvent`s: raw values, smoothed (EMA), extremes/z-scores, and a composite **breadth regime** tag (`risk_on`, `risk_off`, `neutral`) with the rationale. Maintain rolling buffers for the interface.
- Define thresholds in config (e.g., $TICK ±1000 extremes, TRIN bands) — no magic numbers in code.

## 2. `microstructure/cvd.py` — cumulative volume delta
- Reconstruct buy/sell aggressor volume from trade prints (tick rule or exchange aggressor flag if present); publish per-instrument CVD series and CVD divergence vs. price.

## 3. `microstructure/obi.py` — order book imbalance
- From Level 2 book updates, compute top-N-level bid/ask imbalance and its rolling dynamics; publish `OBIEvent`. Degrade to `NO_BOOK` when only Level 1 is available.

## 4. `microstructure/volume_profile.py`
- Session and rolling volume profile; compute POC, value area (VAH/VAL); publish profile snapshots for the heatmap and decision engine.

## 5. `heatmaps/orderbook.py`
- Build a **live order book depth heatmap** matrix (price levels × time, intensity = resting size) from book updates; emit `HeatmapEvent` frames sized for the web canvas; downsample a compact version for the TUI.

## 6. `heatmaps/correlation.py`
- Rolling cross-instrument correlation matrix (NQ/ES/CL/GC + configurable extras) over a config window; emit as a heatmap frame; flag regime shifts (correlation breakdowns).

## 7. `heatmaps/volatility.py`
- Realized-vol surface / term structure per instrument (multiple windows) and a relative-vol heatmap; emit frames.

## 8. `heatmaps/sector.py`
- Optional equity-sector/ETF breadth heatmap (if those symbols are subscribed) for macro context; degrade cleanly if unsubscribed.

**Common contract:** all modules in this phase are wrapped by the single **MarketPulse** agent (per the Master Brief's 15-agent roster), which maintains state in ring buffers, publishes computed events at a throttled cadence, and exposes a `snapshot()` for the interface. All heatmap frames use a normalized `{rows, cols, z, x_labels, y_labels, ts}` schema so the web frontend renders any of them with one Plotly component.

---

## PHASE 03 ACCEPTANCE GATE
- Fed a replay of a session, `breadth.py` emits internals with correct z-scores and a stable regime tag; extremes trigger at configured thresholds.
- `cvd.py` CVD matches a hand-computed value on a small fixture; divergence flag fires on a constructed divergence.
- `obi.py` computes correct imbalance on a synthetic book and returns `NO_BOOK` on L1-only input.
- `volume_profile.py` POC/VAH/VAL correct on a fixture.
- Each heatmap agent emits frames in the common schema at the throttled cadence; `snapshot()` returns render-ready data.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-QUANT (Phase 04) per the dependency graph — no user interaction.
