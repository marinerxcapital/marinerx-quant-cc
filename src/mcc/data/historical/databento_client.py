"""Databento client stub (graceful to cache since no key at build).

Per spec: would pull GLBX.MDP3 1m for NQ/ES etc from .env DATABENTO_KEY.
"""
from __future__ import annotations

import os
import pandas as pd

from .catalog import load_or_synth_nq_bars


def pull_bars(symbol: str = "NQ", freq: str = "1m") -> pd.DataFrame:
    key = os.getenv("DATABENTO_KEY")
    if not key:
        # degrade to cached/synth
        return load_or_synth_nq_bars(symbol=symbol)
    # would use databento here
    return load_or_synth_nq_bars(symbol=symbol)
