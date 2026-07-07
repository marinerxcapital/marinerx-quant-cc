from __future__ import annotations

"""Tradovate connector skeleton for MarinerX Labs.

Design intent:
- Prefer official Tradovate API/OAuth for market data, account state, positions, fills, and orders.
- Use demo/simulation environment for Tradeify accounts unless the user explicitly configures otherwise.
- Keep order placement disabled until MARINERX_ALLOW_LIVE_ORDERS=true and all risk gates pass.

This file is a safe scaffold. Grok/Codex should complete the endpoint mapping against the
current official Tradovate docs inside the target repository.
"""

from dataclasses import dataclass
from typing import Any, Optional

from .base import BrokerAccountMetrics, PositionSnapshot
from .normalizer import stable_hash


@dataclass(frozen=True)
class TradovateConfig:
    environment: str = "demo"  # demo | live
    base_url: str = "https://demo.tradovateapi.com/v1"
    market_data_ws_url: str = "wss://md-demo.tradovateapi.com/v1/websocket"
    app_id: Optional[str] = None
    app_version: Optional[str] = None
    device_id: Optional[str] = None
    cid: Optional[str] = None
    secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class TradovateConnector:
    def __init__(self, config: TradovateConfig):
        self.config = config
        self._access_token: Optional[str] = None

    async def authenticate(self) -> None:
        """Authenticate using official Tradovate API flow.

        Implementation notes for Grok:
        - Support OAuth where available/preferred.
        - Support username/password only via encrypted env/secret manager.
        - Never log username, password, token, account ID, or raw session payload.
        - Validate demo/simulation account before returning success.
        """
        raise NotImplementedError("Implement against current Tradovate auth docs.")

    async def fetch_accounts(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Fetch account list from official Tradovate API.")

    async def fetch_positions(self, account_id: int | str) -> list[PositionSnapshot]:
        raise NotImplementedError("Fetch positions from official Tradovate API.")

    async def fetch_cash_balance(self, account_id: int | str) -> dict[str, Any]:
        raise NotImplementedError("Fetch cash/balance metrics from official Tradovate API.")

    async def fetch_market_snapshot(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError("Subscribe/fetch market snapshot via Tradovate market data websocket.")

    async def build_broker_metrics(self, account_id: int | str, account_name: str = "Tradeify Tradovate") -> BrokerAccountMetrics:
        """Convert Tradovate account responses into MarinerX broker metrics.

        Grok should replace placeholders with parsed API fields.
        """
        balance_payload = await self.fetch_cash_balance(account_id)
        positions = await self.fetch_positions(account_id)

        balance = float(balance_payload.get("balance", 150_000.0))
        realized_day_pnl = float(balance_payload.get("realizedDayPnl", 0.0))
        unrealized_pnl = float(balance_payload.get("unrealizedPnl", 0.0))

        return BrokerAccountMetrics(
            source="tradovate_api",
            account_name=account_name,
            account_id_hash=stable_hash(str(account_id)),
            balance=balance,
            net_liq=balance_payload.get("netLiq"),
            cash_balance=balance_payload.get("cashBalance"),
            realized_day_pnl=realized_day_pnl,
            unrealized_pnl=unrealized_pnl,
            open_trade_risk=0.0,
            eod_drawdown_floor=balance_payload.get("eodDrawdownFloor"),
            positions=positions,
            raw={"balance_keys": sorted(balance_payload.keys())},
        )
