"""Ring buffers for live series (Phase 01/02)."""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, List


class RingBuffer:
    """Thread/async safe-ish ring for recent data."""
    def __init__(self, maxsize: int = 5000) -> None:
        self.maxsize = maxsize
        self._buf: Deque[Any] = deque(maxlen=maxsize)

    def append(self, item: Any) -> None:
        self._buf.append(item)

    def get(self, n: int | None = None) -> List[Any]:
        if n is None:
            return list(self._buf)
        return list(self._buf)[-n:]

    def __len__(self) -> int:
        return len(self._buf)
