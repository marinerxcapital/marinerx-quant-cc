"""Market breadth from TICK/TRIN proxies (exchange or free-market derived)."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from mcc.core.events import InternalsEvent

# Configurable thresholds (no magic numbers inline)
TICK_EXTREME = 1000.0
TRIN_RISK_ON_MAX = 0.85
TRIN_RISK_OFF_MIN = 1.15
BREADTH_RISK_ON = 60.0
BREADTH_RISK_OFF = 40.0
EMA_ALPHA = 0.2
ZSCORE_WINDOW = 20


@dataclass
class BreadthState:
    tick: float
    trin: float
    add: float
    vold: str
    breadth_score: float
    regime: str
    rationale: str
    tick_ema: float
    trin_ema: float
    tick_z: float
    trin_z: float
    extremes: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "trin": self.trin,
            "add": self.add,
            "vold": self.vold,
            "breadth_score": self.breadth_score,
            "regime": self.regime,
            "rationale": self.rationale,
            "tick_ema": self.tick_ema,
            "trin_ema": self.trin_ema,
            "tick_z": self.tick_z,
            "trin_z": self.trin_z,
            "extremes": self.extremes,
        }


def _ema(prev: float, value: float, alpha: float = EMA_ALPHA) -> float:
    return alpha * value + (1.0 - alpha) * prev


def _zscore(history: deque[float], value: float) -> float:
    if len(history) < 2:
        return 0.0
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / len(history)
    std = math.sqrt(var) if var > 0 else 1.0
    return (value - mean) / std


def _regime_from_breadth(breadth_score: float, tick: float, trin: float) -> tuple[str, str]:
    extremes: list[str] = []
    if abs(tick) >= TICK_EXTREME:
        extremes.append(f"TICK extreme ({tick:+.0f})")
    if trin <= TRIN_RISK_ON_MAX:
        extremes.append(f"TRIN risk-on ({trin:.2f})")
    elif trin >= TRIN_RISK_OFF_MIN:
        extremes.append(f"TRIN risk-off ({trin:.2f})")

    if breadth_score >= BREADTH_RISK_ON and trin <= 1.0:
        regime = "risk_on"
        rationale = "breadth supportive; " + (", ".join(extremes) if extremes else "internals aligned")
    elif breadth_score < BREADTH_RISK_OFF or trin >= TRIN_RISK_OFF_MIN:
        regime = "risk_off"
        rationale = "breadth weak; " + (", ".join(extremes) if extremes else "internals cautious")
    else:
        regime = "neutral"
        rationale = "mixed internals; " + (", ".join(extremes) if extremes else "no clear edge")

    return regime, rationale


def compute_breadth_from_proxies(
    proxies: dict[str, Any],
    *,
    breadth_score: float | None = None,
    prev_tick_ema: float | None = None,
    prev_trin_ema: float | None = None,
    tick_history: deque[float] | None = None,
    trin_history: deque[float] | None = None,
) -> BreadthState:
    """Compute breadth state from TICK/TRIN/ADD proxy dict."""
    tick = float(proxies.get("tick", 0))
    trin = float(proxies.get("trin", 1.0))
    add = float(proxies.get("add", 0))
    vold = str(proxies.get("vold", "1.0:1"))
    score = float(breadth_score if breadth_score is not None else proxies.get("breadth_score", 50))

    tick_ema = _ema(prev_tick_ema if prev_tick_ema is not None else tick, tick)
    trin_ema = _ema(prev_trin_ema if prev_trin_ema is not None else trin, trin)

    th = tick_history or deque(maxlen=ZSCORE_WINDOW)
    rh = trin_history or deque(maxlen=ZSCORE_WINDOW)
    th.append(tick)
    rh.append(trin)

    regime, rationale = _regime_from_breadth(score, tick, trin)
    extremes = {
        "tick_high": tick >= TICK_EXTREME,
        "tick_low": tick <= -TICK_EXTREME,
        "trin_risk_on": trin <= TRIN_RISK_ON_MAX,
        "trin_risk_off": trin >= TRIN_RISK_OFF_MIN,
    }

    return BreadthState(
        tick=tick,
        trin=trin,
        add=add,
        vold=vold,
        breadth_score=score,
        regime=regime,
        rationale=rationale,
        tick_ema=round(tick_ema, 2),
        trin_ema=round(trin_ema, 3),
        tick_z=round(_zscore(th, tick), 3),
        trin_z=round(_zscore(rh, trin), 3),
        extremes=extremes,
    )


def compute_breadth_from_bar(bar: dict[str, Any]) -> BreadthState:
    """Derive TICK/TRIN proxies from a bar payload (offline/replay friendly)."""
    if "proxies" in bar:
        return compute_breadth_from_proxies(bar["proxies"], breadth_score=bar.get("breadth_score"))

    close = float(bar.get("c", bar.get("close", 0)) or 0)
    open_ = float(bar.get("o", bar.get("open", close)) or close)
    high = float(bar.get("h", bar.get("high", close)) or close)
    low = float(bar.get("l", bar.get("low", close)) or close)

    if close == 0 and open_ == 0:
        return compute_breadth_from_proxies({"tick": 0, "trin": 1.0, "add": 0, "vold": "1.0:1", "breadth_score": 50})

    momentum_pct = ((close - open_) / open_ * 100.0) if open_ else 0.0
    range_pct = ((high - low) / close * 100.0) if close else 0.0

    tick_proxy = round(momentum_pct * 80 + (close - open_), 1)
    trin_proxy = round(max(0.4, min(2.0, 1.0 - momentum_pct / 5)), 2)
    add_proxy = round(max(0, momentum_pct) * 150, 1)
    breadth_score = round(50 + momentum_pct * 10 + (10 if close > open_ else -10), 1)
    breadth_score = max(0.0, min(100.0, breadth_score))

    proxies = {
        "tick": tick_proxy,
        "trin": trin_proxy,
        "add": add_proxy,
        "vold": f"{1.0 + range_pct / 10:.1f}:1",
        "breadth_score": breadth_score,
    }
    return compute_breadth_from_proxies(proxies, breadth_score=breadth_score)


def breadth_to_internals_events(
    state: BreadthState,
    *,
    ts_utc: Any,
    source: str,
    symbol: str = "MARKET",
) -> list[InternalsEvent]:
    """Publish rolling internals as InternalsEvent sequence."""
    base = state.to_dict()
    events = [
        InternalsEvent(ts_utc, source, "breadth_score", state.breadth_score, symbol=symbol, **base),
        InternalsEvent(ts_utc, source, "tick", state.tick, symbol=symbol, smoothed=state.tick_ema, z=state.tick_z),
        InternalsEvent(ts_utc, source, "trin", state.trin, symbol=symbol, smoothed=state.trin_ema, z=state.trin_z),
        InternalsEvent(ts_utc, source, "regime", 0.0, symbol=symbol, regime=state.regime, rationale=state.rationale),
    ]
    return events


class BreadthComputer:
    """Stateful breadth engine with ring buffers for UI snapshot()."""

    def __init__(self, window: int = ZSCORE_WINDOW) -> None:
        self._tick_hist: deque[float] = deque(maxlen=window)
        self._trin_hist: deque[float] = deque(maxlen=window)
        self._states: deque[BreadthState] = deque(maxlen=100)
        self._tick_ema: float | None = None
        self._trin_ema: float | None = None
        self._last: BreadthState | None = None

    def update_from_bar(self, bar: dict[str, Any]) -> BreadthState:
        if "proxies" in bar:
            state = compute_breadth_from_proxies(
                bar["proxies"],
                breadth_score=bar.get("breadth_score"),
                prev_tick_ema=self._tick_ema,
                prev_trin_ema=self._trin_ema,
                tick_history=self._tick_hist,
                trin_history=self._trin_hist,
            )
        else:
            state = compute_breadth_from_bar(bar)
            # Re-run with history for EMA/z when incremental
            state = compute_breadth_from_proxies(
                {
                    "tick": state.tick,
                    "trin": state.trin,
                    "add": state.add,
                    "vold": state.vold,
                    "breadth_score": state.breadth_score,
                },
                breadth_score=state.breadth_score,
                prev_tick_ema=self._tick_ema,
                prev_trin_ema=self._trin_ema,
                tick_history=self._tick_hist,
                trin_history=self._trin_hist,
            )

        self._tick_ema = state.tick_ema
        self._trin_ema = state.trin_ema
        self._last = state
        self._states.append(state)
        return state

    def update_from_free_market(self) -> BreadthState:
        from mcc.data.live.free_market import get_internals_proxy

        data = get_internals_proxy()
        proxies = data.get("proxies", {})
        state = compute_breadth_from_proxies(
            proxies,
            breadth_score=data.get("breadth_score"),
            prev_tick_ema=self._tick_ema,
            prev_trin_ema=self._trin_ema,
            tick_history=self._tick_hist,
            trin_history=self._trin_hist,
        )
        self._tick_ema = state.tick_ema
        self._trin_ema = state.trin_ema
        self._last = state
        self._states.append(state)
        return state

    def snapshot(self) -> dict[str, Any]:
        if self._last is None:
            return {"regime": "neutral", "breadth_score": 50, "buffer_len": 0}
        return {**self._last.to_dict(), "buffer_len": len(self._states)}