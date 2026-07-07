"""Human-paced browser interactions."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from tradeify_sync.config import Settings


async def human_pause(settings: Settings) -> None:
    """Sleep a random duration within configured bounds."""
    delay_ms = random.randint(settings.browser.min_delay_ms, settings.browser.max_delay_ms)
    await asyncio.sleep(delay_ms / 1000.0)


async def human_scroll(page: Any) -> None:
    """Perform a small randomized scroll."""
    delta = random.randint(100, 400) * random.choice([-1, 1])
    await page.mouse.wheel(0, delta)
    await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_move(page: Any, selector: str) -> None:
    """Move cursor toward an element before interacting."""
    try:
        box = await page.locator(selector).first.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.05, 0.2))
    except Exception:
        pass