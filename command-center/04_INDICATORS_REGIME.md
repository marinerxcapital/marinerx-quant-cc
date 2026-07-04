# PHASE 04 — INDICATOR & SIGNAL ENGINE · REGIME DETECTION

**CONTEXT:** Data + internals/microstructure/heatmaps complete. Build the indicator computation layer (works identically on historical arrays and live bus streams) and regime classification. Indicators produce typed signals consumed by strategies and the decision engine.

---

## 1. `indicators/library.py`
- A registry of pure, vectorized indicator functions operating on `polars`/`numpy` frames: moving averages (SMA/EMA/WMA/HMA), ATR, RSI, MACD, Bollinger/Keltner, VWAP + bands, ADX, Donchian/opening range, anchored VWAP, and microstructure-aware ones (CVD-based, volume-profile-based) that read Phase-03 outputs.
- Each indicator: typed params (pydantic), declared inputs/outputs, `compute(df, params) -> df`, and a `warmup` length. No look-ahead — enforce that outputs at time *t* use only data ≤ *t* (unit-tested).
- Support **custom user indicators** via a plugin interface: drop a module implementing the indicator protocol into `strategies/indicators/` and it auto-registers.

## 2. `indicators/engine.py`
- `IndicatorEngine`: given a config of active indicators per instrument, computes them (a) batch over historical frames for backtests/research and (b) incrementally on live bus bars, publishing `IndicatorEvent`s and updating ring buffers for the interface. Guarantees identical values in batch vs. incremental mode (parity test).
- Wrapped by `IndicatorEngine` agent.

## 3. `regime/volatility_regime.py`
- Classify volatility regime per instrument (e.g., realized-vol terciles, ATR percentile) → `low/normal/high`; publish `RegimeEvent`.

## 4. `regime/hmm.py`
- Hidden Markov Model (Gaussian, via `hmmlearn` or a `statsmodels`/custom EM implementation — pin the dependency) on returns/vol features to label `trending` vs `mean-reverting`/`ranging` states with posterior probabilities; retrain on a schedule; publish state + confidence. Persist fitted models; never refit inside the live loop.
- Wrapped by `RegimeMonitor` agent, which publishes a consolidated regime snapshot (vol regime + HMM state + breadth regime from Phase 03) that the decision engine consumes.

---

## PHASE 04 ACCEPTANCE GATE
- No-look-ahead test passes for every library indicator (shifting future data does not change past outputs).
- Batch vs. incremental parity: engine produces identical indicator series when fed a frame at once vs. bar-by-bar over the bus (assert within float tolerance).
- A custom indicator dropped into the plugin folder auto-registers and computes.
- `volatility_regime` and `hmm` label a labeled synthetic series (constructed trending vs ranging segments) with expected majority states; HMM posteriors sum to 1.
- `ruff` + `mypy --strict src/` clean.

Self-verify against this Acceptance Gate + `ruff` + `mypy --strict src/` + relevant `pytest`. Report PASS/FAIL with evidence to Build Manager. On PASS, Build Manager advances to SA-STRAT (Phase 05) per the dependency graph — no user interaction.
