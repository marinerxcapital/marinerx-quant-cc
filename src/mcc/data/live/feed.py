"""LiveFeed Protocol + FeedAgent per 02_DATA_LAYER.md.

All adapters (replay, databento_live, iqfeed, tradovate) implement this.
Consumers depend only on the protocol; switching adapters is transparent.
"""
from __future__ import annotations

from typing import AsyncIterator, Protocol, Sequence, Any, runtime_checkable

from mcc.core.bus import MessageBus
from mcc.core.clock import Clock
from mcc.core.events import BarEvent, TickEvent, InternalsEvent


@runtime_checkable
class LiveFeed(Protocol):
    async def connect(self) -> None: ...
    async def subscribe(self, symbols: Sequence[str], channels: Sequence[str]) -> None: ...
    async def stream(self) -> AsyncIterator[BarEvent | TickEvent | InternalsEvent | Any]: ...
    async def disconnect(self) -> None: ...


class FeedAgent:
    """Wraps active feed, publishes normalized events to bus, writes to buffers + parquet (stub)."""
    def __init__(self, feed: Any, bus: MessageBus, clock: Clock) -> None:
        self.feed = feed
        self.bus = bus
        self.clock = clock
        self.running = False

    async def run(self, symbols: Sequence[str] = ("NQ",), channels: Sequence[str] = ("bars",)) -> None:
        self.running = True
        await self.feed.connect()
        await self.feed.subscribe(symbols, channels)
        async for ev in self.feed.stream():
            if not self.running:
                break
            await self.bus.publish(ev)
            # also could append to ring buffers here
        await self.feed.disconnect()

    async def stop(self) -> None:
        self.running = False


# Note: concrete adapters subclass or implement the protocol methods.
