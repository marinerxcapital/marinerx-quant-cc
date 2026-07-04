"""Continuous contract roll per spec (volume/OI based).

For this build (single front-month synth data), roll is identity + tags a roll date.
Document: Roll rule = switch to next contract on first notice or volume crossover.
"""
from __future__ import annotations

import pandas as pd


def stitch_continuous(df: pd.DataFrame, symbol: str = "NQ") -> pd.DataFrame:
    """Identity stitch for synthetic; tags 'roll' on first bar of day 3 for demo."""
    out = df.copy()
    out["continuous_symbol"] = symbol
    if len(out) > 2:
        # tag a synthetic roll date
        out.loc[out.index[2], "roll"] = True
    out["roll_rule"] = "volume_crossover_or_first_notice_demo"
    return out
