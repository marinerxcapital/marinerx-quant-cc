# Phase 16 API Contracts

## Unchanged bus events

### RiskState (`risk/monitor.py`)

```python
@dataclass
class RiskState:
    ts_utc: datetime
    source: str
    equity: Decimal
    risk_level: RiskLevel
    position_size: int
    size_reason: str
    var: float
    es: float
    var_breach: bool
    exposure_gross: Decimal
    exposure_net: Decimal
    veto: bool
    veto_reason: Optional[str]
    details: Dict[str, Any]
```

**Before/after:** identical. Phase 16 only changes internal sizing/VaR computation paths.

### RegimeEvent (`core/events.py`)

```python
payload = {
    "type": "regime",
    "symbol": str,
    "state": str,       # e.g. "trending", "mean-reverting"
    "confidence": float, # 0.0–1.0
    # optional diagnostics via **kw
}
```

**Before/after:** shape preserved. Engine changed from hmmlearn to statsmodels MarkovRegression.

### DecisionEvent (`core/events.py`)

```python
payload = {
    "symbol": str,
    "decision": str,  # "GO" | "NO_GO"
    "reason": str,
    "size": int,
}
```

**Before/after:** unchanged.

## Preserved public function signatures

| Module | Function | Signature unchanged |
|---|---|---|
| `risk/sizing.py` | `kelly_size`, `vol_target_size`, `compute_size` | ✓ |
| `risk/var_es.py` | `historical_var_es`, `var_es_from_pnl_series` | ✓ (+ optional `use_riskfolio` kwarg) |
| `decision/engine.py` | `decide()` | ✓ |

## Sharpe / Sortino / Calmar basis note

QuantStats computes these on **daily return periods** derived from the trade blotter (`trades_to_return_series`), not on individual round-turn trades. A strategy with few trades but long holding periods will show different per-trade vs per-period statistics. Reports label the benchmark as `flat_rate_4.5pct` (not an equity index).

## Export schemas

- Section 8.1 — `reports_out/allocations/*.json`
- Section 8.2 — `reports_out/tear_sheets/*_metrics.json`
- Section 8.3 — `research/stat_models.py` → `StatisticalModelResult.to_dict()`