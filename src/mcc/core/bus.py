"""MessageBus: async in-process pub/sub per spec.

subscribe(topic) yields matching events. Supports wildcard-ish via exact for now.
Bounded queues, drop-oldest, dropped count.
"""
from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import AsyncIterator, Any, Set, Optional
# Events imported for type narrowing if needed; use Any for flexibility under strict


class MessageBus:
    def __init__(self, max_queue: int = 10000):
        self._subs: dict[str, Set[asyncio.Queue[Any]]] = defaultdict(set)
        self._all_subs: Set[asyncio.Queue[Any]] = set()
        self.dropped = 0
        self.max_queue = max_queue
        self._lock = asyncio.Lock()

    async def publish(self, ev: Any) -> None:
        """Publish to topic subscribers and global."""
        topic = getattr(ev, "topic", "default") if hasattr(ev, "topic") else str(type(ev))
        async with self._lock:
            targets = list(self._subs.get(str(topic), set())) + list(self._all_subs)
            for q in targets:
                try:
                    if q.full():
                        # drop oldest
                        try:
                            q.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        self.dropped += 1
                    q.put_nowait(ev)
                except Exception:
                    self.dropped += 1

    async def subscribe(self, topic: Optional[str] = None, topics: Optional[list[str]] = None) -> AsyncIterator[Any]:
        """Async iterator over events for topic(s) or all if None."""
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=self.max_queue)
        tlist: list[str] = []
        if topics:
            tlist = [str(t) for t in topics]
        elif topic:
            tlist = [str(topic)]
        async with self._lock:
            if tlist:
                for t in tlist:
                    self._subs[t].add(q)
            else:
                self._all_subs.add(q)
        try:
            while True:
                ev = await q.get()
                # filter if specific but since we put only matching, yield all
                if hasattr(ev, "topic"):
                    ev_topic = str(getattr(ev, "topic", ""))
                    if not tlist or ev_topic in tlist or ev_topic == topic:
                        yield ev
                    else:
                        yield ev
                else:
                    yield ev
        finally:
            async with self._lock:
                for t in tlist:
                    self._subs[t].discard(q)
                self._all_subs.discard(q)
