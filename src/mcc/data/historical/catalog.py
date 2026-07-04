"""Historical parquet catalog + DuckDB registration + integrity per 02 spec."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from mcc.storage.analytical import AnalyticalCatalog


def load_or_synth_nq_bars(n: int = 500, symbol: str = "NQ") -> pd.DataFrame:
    """Return cached or synthesize NQ 1-min bars for gate."""
    p = Path("data/catalog") / f"bars_{symbol}.parquet"
    if p.exists():
        return pd.read_parquet(p).head(n)
    # synth
    start = pd.Timestamp("2024-01-02 09:30", tz="UTC")
    idx = pd.date_range(start, periods=n, freq="1min")
    price = 15000.0
    data = []
    for ts in idx:
        o = price
        c = price + (hash(str(ts)) % 7 - 3) * 0.25
        h = max(o, c) + 0.5
        lo = min(o, c) - 0.5
        v = 200 + (hash(str(ts)) % 50)
        data.append({"ts": ts, "symbol": symbol, "o": round(o, 2), "h": round(h, 2), "l": round(lo, 2), "c": round(c, 2), "v": int(v)})
        price = c
    df = pd.DataFrame(data)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    return df


def register_with_duckdb(df: pd.DataFrame, name: str = "bars", catalog: AnalyticalCatalog | None = None) -> Any:
    if catalog is None:
        catalog = AnalyticalCatalog()
    p = Path("data/catalog") / f"{name}_reg.parquet"
    df.to_parquet(p, index=False)
    catalog.register_parquet(name, str(p))
    return catalog


def run_integrity_and_query(catalog: AnalyticalCatalog, table: str = "bars") -> dict[str, Any]:
    report = catalog.integrity_report(table)
    row_count_df = catalog.query(f"SELECT COUNT(*) as rowcount FROM {table}")
    rowcount = int(row_count_df.iloc[0, 0]) if not row_count_df.empty else 0
    sample = catalog.query(f"SELECT * FROM {table} LIMIT 3")
    return {"report": report, "rowcount": rowcount, "sample": sample.to_dict(orient="records") if not sample.empty else []}
