from __future__ import annotations

"""Tradovate official API connector — demo environment by default."""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from .base import BrokerAccountMetrics, PositionSnapshot
from .normalizer import stable_hash

DEMO_BASE_URL = "https://demo.tradovateapi.com/v1"
LIVE_BASE_URL = "https://live.tradovateapi.com/v1"


class TradovateError(Exception):
    """Base Tradovate connector error (no secrets in message)."""


class TradovateConfigurationError(TradovateError):
    """Missing or invalid Tradovate configuration."""


class TradovateAuthError(TradovateError):
    """Authentication failed."""


@dataclass(frozen=True)
class TradovateConfig:
    environment: str = "demo"
    base_url: str = DEMO_BASE_URL
    market_data_ws_url: str = "wss://md-demo.tradovateapi.com/v1/websocket"
    app_id: Optional[str] = None
    app_version: Optional[str] = None
    device_id: Optional[str] = None
    cid: Optional[str] = None
    secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    account_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> TradovateConfig:
        env = os.getenv("MARINERX_TRADOVATE_ENVIRONMENT", "demo").strip().lower()
        base = os.getenv("TRADOVATE_BASE_URL") or (DEMO_BASE_URL if env == "demo" else LIVE_BASE_URL)
        ws = os.getenv("TRADOVATE_MD_WS_URL") or (
            "wss://md-demo.tradovateapi.com/v1/websocket"
            if env == "demo"
            else "wss://md.tradovateapi.com/v1/websocket"
        )
        return cls(
            environment=env,
            base_url=base.rstrip("/"),
            market_data_ws_url=ws,
            app_id=os.getenv("TRADOVATE_APP_ID") or None,
            app_version=os.getenv("TRADOVATE_APP_VERSION") or None,
            device_id=os.getenv("TRADOVATE_DEVICE_ID") or None,
            cid=os.getenv("TRADOVATE_CID") or None,
            secret=os.getenv("TRADOVATE_SECRET") or None,
            username=os.getenv("TRADOVATE_USERNAME") or None,
            password=os.getenv("TRADOVATE_PASSWORD") or None,
            account_id=os.getenv("TRADOVATE_ACCOUNT_ID") or None,
        )

    def validate_credentials(self) -> None:
        missing = []
        if not self.cid:
            missing.append("TRADOVATE_CID")
        if not self.secret:
            missing.append("TRADOVATE_SECRET")
        if not self.username:
            missing.append("TRADOVATE_USERNAME")
        if not self.password:
            missing.append("TRADOVATE_PASSWORD")
        if missing:
            raise TradovateConfigurationError(
                f"Tradovate API credentials not configured. Set: {', '.join(missing)}"
            )


class TradovateConnector:
    def __init__(self, config: TradovateConfig, *, client: httpx.AsyncClient | None = None):
        self.config = config
        self._access_token: Optional[str] = None
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
            self._owns_client = True
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def authenticate(self) -> None:
        self.config.validate_credentials()
        client = await self._get_client()
        payload = {
            "name": self.config.username,
            "password": self.config.password,
            "appId": self.config.app_id or "MarinerX",
            "appVersion": self.config.app_version or "1.0",
            "cid": int(self.config.cid) if self.config.cid and self.config.cid.isdigit() else self.config.cid,
            "sec": self.config.secret,
            "deviceId": self.config.device_id or "marinerx-labs",
        }
        url = f"{self.config.base_url}/auth/accesstokenrequest"
        try:
            resp = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise TradovateAuthError("Tradovate authentication request failed") from exc
        if resp.status_code >= 400:
            raise TradovateAuthError(f"Tradovate authentication rejected (HTTP {resp.status_code})")
        data = resp.json()
        token = data.get("accessToken") or data.get("access_token")
        if not token:
            raise TradovateAuthError("Tradovate authentication response missing access token")
        self._access_token = str(token)

    def _headers(self) -> dict[str, str]:
        if not self._access_token:
            raise TradovateAuthError("Tradovate connector not authenticated")
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _get(self, path: str) -> Any:
        client = await self._get_client()
        url = f"{self.config.base_url}{path}"
        resp = await client.get(url, headers=self._headers())
        if resp.status_code >= 400:
            raise TradovateError(f"Tradovate API error on {path} (HTTP {resp.status_code})")
        return resp.json()

    async def fetch_accounts(self) -> list[dict[str, Any]]:
        if not self._access_token:
            await self.authenticate()
        data = await self._get("/account/list")
        if isinstance(data, list):
            return data
        return data.get("accounts", data.get("items", []))

    def select_account(self, accounts: list[dict[str, Any]]) -> dict[str, Any]:
        if self.config.account_id:
            for acct in accounts:
                if str(acct.get("id")) == str(self.config.account_id):
                    return acct
        for acct in accounts:
            name = str(acct.get("name", "")).upper()
            if "150" in name or "TRADEIFY" in name or "SELECT" in name:
                return acct
        if accounts:
            return accounts[0]
        raise TradovateError("No Tradovate accounts returned")

    async def fetch_cash_balance(self, account_id: int | str) -> dict[str, Any]:
        if not self._access_token:
            await self.authenticate()
        data = await self._get("/cashBalance/list")
        items = data if isinstance(data, list) else data.get("items", [])
        for item in items:
            if str(item.get("accountId")) == str(account_id):
                return self._parse_balance(item)
        if items:
            return self._parse_balance(items[0])
        return {"balance": 0.0, "realizedDayPnl": 0.0, "unrealizedPnl": 0.0}

    @staticmethod
    def _parse_balance(item: dict[str, Any]) -> dict[str, Any]:
        balance = float(item.get("amount") or item.get("balance") or item.get("totalCashValue") or 0.0)
        realized = float(item.get("realizedPnL") or item.get("realizedDayPnl") or item.get("dayPnL") or 0.0)
        unrealized = float(item.get("unrealizedPnL") or item.get("openPnL") or 0.0)
        net_liq = float(item.get("netLiq") or item.get("netLiquidation") or balance)
        floor = item.get("eodDrawdownFloor") or item.get("drawdownFloor")
        return {
            "balance": balance,
            "netLiq": net_liq,
            "cashBalance": item.get("cashBalance") or balance,
            "realizedDayPnl": realized,
            "unrealizedPnl": unrealized,
            "eodDrawdownFloor": float(floor) if floor is not None else None,
        }

    async def fetch_positions(self, account_id: int | str) -> list[PositionSnapshot]:
        if not self._access_token:
            await self.authenticate()
        data = await self._get("/position/list")
        items = data if isinstance(data, list) else data.get("items", [])
        out: list[PositionSnapshot] = []
        for item in items:
            if str(item.get("accountId")) != str(account_id):
                continue
            qty = int(item.get("netPos") or item.get("quantity") or 0)
            if qty == 0:
                continue
            out.append(
                PositionSnapshot(
                    symbol=str(item.get("contractSymbol") or item.get("symbol") or "UNKNOWN"),
                    net_quantity=qty,
                    average_price=_float_or_none(item.get("netPrice") or item.get("avgPrice")),
                    unrealized_pnl=_float_or_none(item.get("openPnL") or item.get("unrealizedPnL")),
                )
            )
        return out

    async def fetch_fills(self, account_id: int | str) -> list[dict[str, Any]]:
        if not self._access_token:
            await self.authenticate()
        data = await self._get("/fill/list")
        items = data if isinstance(data, list) else data.get("items", [])
        return [f for f in items if str(f.get("accountId")) == str(account_id)]

    async def fetch_market_snapshot(self, symbol: str) -> dict[str, Any]:
        if not self._access_token:
            await self.authenticate()
        try:
            data = await self._get(f"/md/getChart?symbol={symbol}&chartDescription=1m")
            return {"symbol": symbol, "source": "tradovate_md", "data": data}
        except TradovateError:
            return {"symbol": symbol, "source": "tradovate_md", "data": None, "note": "market_data_unavailable"}

    async def build_broker_metrics(
        self,
        account_id: int | str,
        account_name: str = "Tradeify Tradovate",
    ) -> BrokerAccountMetrics:
        balance_payload = await self.fetch_cash_balance(account_id)
        positions = await self.fetch_positions(account_id)
        open_risk = sum(abs(p.unrealized_pnl or 0.0) for p in positions)

        return BrokerAccountMetrics(
            source="tradovate_api",
            account_name=account_name,
            account_id_hash=stable_hash(str(account_id)),
            balance=float(balance_payload.get("balance", 0.0)),
            net_liq=balance_payload.get("netLiq"),
            cash_balance=balance_payload.get("cashBalance"),
            realized_day_pnl=float(balance_payload.get("realizedDayPnl", 0.0)),
            unrealized_pnl=float(balance_payload.get("unrealizedPnl", 0.0)),
            open_trade_risk=open_risk,
            eod_drawdown_floor=balance_payload.get("eodDrawdownFloor"),
            positions=positions,
            raw={"balance_keys": sorted(balance_payload.keys()), "position_count": len(positions)},
        )


def _float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None