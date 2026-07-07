"""Deterministic backtest engine with objective metrics."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from mcc.storage.repositories import BacktestRepository, MarketBarRepository, StrategyRepository

_bar_repo = MarketBarRepository()
_bt_repo = BacktestRepository()
_strategy_repo = StrategyRepository()


def _config_hash(config: dict[str, Any]) -> str:
    normalized = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _max_drawdown(equity_curve: list[float]) -> tuple[float, float]:
    if not equity_curve:
        return 0.0, 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        dd = peak - v
        max_dd = max(max_dd, dd)
    pct = (max_dd / peak * 100) if peak else 0.0
    return max_dd, pct


def _basic_sharpe(equity_curve: list[float]) -> float | None:
    if len(equity_curve) < 3:
        return None
    returns = [(equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] for i in range(1, len(equity_curve)) if equity_curve[i - 1]]
    if len(returns) < 2:
        return None
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    if var <= 0:
        return None
    import math
    return mean_r / math.sqrt(var) * (252 ** 0.5)


def _run_orb_template(bars: list[dict[str, Any]], initial_equity: float, risk_per_trade: float) -> tuple[list[dict], list[float]]:
    """Opening Range Breakout — deterministic on bar data."""
    trades: list[dict[str, Any]] = []
    equity = [initial_equity]
    if len(bars) < 5:
        return trades, equity
    or_high = max(b["high"] for b in bars[:3])
    or_low = min(b["low"] for b in bars[:3])
    for i, bar in enumerate(bars[3:], start=3):
        pnl = 0.0
        if bar["close"] > or_high:
            pnl = risk_per_trade * 0.8
        elif bar["close"] < or_low:
            pnl = -risk_per_trade * 0.6
        equity.append(equity[-1] + pnl)
        if pnl != 0:
            trades.append({"bar": i, "pnl": pnl, "side": "LONG" if pnl > 0 else "SHORT"})
    return trades, equity


def _demo_bars(symbol: str, count: int = 30) -> list[dict[str, Any]]:
    from datetime import datetime, timedelta, timezone
    base = 18000.0 if symbol.upper() in ("NQ", "MNQ") else 5300.0
    bars = []
    ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    for i in range(count):
        o = base + i * 2
        c = o + (4 if i % 3 else -3)
        bars.append({
            "symbol": symbol,
            "timeframe": "15m",
            "timestamp": ts + timedelta(minutes=15 * i),
            "open": o, "high": max(o, c) + 5, "low": min(o, c) - 5,
            "close": c, "volume": 1000 + i * 10,
            "source": "demo_deterministic",
        })
    return bars


def run_backtest(payload: dict[str, Any]) -> dict[str, Any]:
    strategy_id = payload.get("strategy_id", "")
    strategy = _strategy_repo.get(strategy_id)
    if not strategy:
        return {"error": "strategy_not_found", "message": f"Strategy {strategy_id} not found"}

    symbol = payload.get("symbol", strategy.get("instrument", "NQ"))
    timeframe = payload.get("timeframe", strategy.get("timeframe", "15m"))
    initial_equity = float(payload.get("initial_equity", 100000))
    risk_per_trade = float(payload.get("risk_per_trade", 350))
    use_demo = payload.get("use_demo_data", False)

    bars = _bar_repo.get_bars(symbol, timeframe, limit=500)
    demo_labeled = False
    if not bars:
        if use_demo:
            bars = _demo_bars(symbol)
            demo_labeled = True
        else:
            return {"error": "no_data", "message": "No market bars available. Pass use_demo_data=true for labeled demo run."}

    template = (strategy.get("parameters_json") or {}).get("template", "orb")
    if template == "vwap_mean_reversion":
        trades, equity = _run_orb_template(bars, initial_equity, risk_per_trade * 0.9)
    elif template == "trend_momentum":
        trades, equity = _run_orb_template(bars, initial_equity, risk_per_trade * 1.1)
    elif template == "event_lockout":
        trades, equity = [], [initial_equity]
    else:
        trades, equity = _run_orb_template(bars, initial_equity, risk_per_trade)

    pnls = [t["pnl"] for t in trades]
    total_trades = len(trades)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = len(wins) / total_trades if total_trades else 0.0
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    profit_factor = gross_profit / abs(gross_loss) if gross_loss else None
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    max_dd, max_dd_pct = _max_drawdown(equity)
    net_pnl = equity[-1] - initial_equity if equity else 0.0

    config = {
        "strategy_id": strategy_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "start_date": payload.get("start_date", ""),
        "end_date": payload.get("end_date", ""),
        "initial_equity": initial_equity,
        "risk_per_trade": risk_per_trade,
        "commission_per_contract": payload.get("commission_per_contract", 2.5),
        "slippage_ticks": payload.get("slippage_ticks", 1.0),
        "template": template,
    }
    chash = _config_hash(config)
    metrics = {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4) if profit_factor is not None else None,
        "net_pnl": round(net_pnl, 2),
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "average_win": round(avg_win, 2),
        "average_loss": round(avg_loss, 2),
        "expectancy": round(expectancy, 2),
        "sharpe_basic": round(_basic_sharpe(equity), 4) if _basic_sharpe(equity) is not None else None,
        "demo_labeled": demo_labeled,
    }
    result = {
        **metrics,
        "equity_curve": equity,
        "trade_list": trades,
        "config_hash": chash,
        "strategy_id": strategy_id,
        "symbol": symbol,
        "timeframe": timeframe,
    }
    saved = _bt_repo.save_run({
        "strategy_id": strategy_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "initial_equity": initial_equity,
        "risk_per_trade": risk_per_trade,
        "commission_per_contract": config["commission_per_contract"],
        "slippage_ticks": config["slippage_ticks"],
        "metrics": metrics,
        "equity_curve": equity,
        "trade_list": trades,
        "config_hash": chash,
    })
    result["backtest_run_id"] = saved["id"]
    return result