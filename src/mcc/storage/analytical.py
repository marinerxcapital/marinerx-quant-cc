"""DuckDB analytical catalog over parquet for Phase 02.

Register datasets, run SQL, integrity helpers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import duckdb
import pandas as pd


class AnalyticalCatalog:
    def __init__(self, base_dir: Path | str = "data/catalog") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(database=":memory:")
        self._registered: dict[str, str] = {}

    def register_parquet(self, name: str, glob_path: str) -> None:
        """Register parquet dataset with DuckDB."""
        self.con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{glob_path}')")
        self._registered[name] = glob_path

    def query(self, sql: str) -> Any:
        return self.con.execute(sql).df()

    def integrity_report(self, table: str = "bars") -> dict[str, Any]:
        """Basic gap/duplicate checks."""
        try:
            df = self.query(f"SELECT symbol, ts, COUNT(*) as cnt FROM {table} GROUP BY symbol, ts HAVING cnt > 1")
            dups = len(df)
            gaps_sql = f"""
            WITH ordered AS (
                SELECT symbol, ts, LEAD(ts) OVER (PARTITION BY symbol ORDER BY ts) as next_ts
                FROM {table}
            )
            SELECT symbol, COUNT(*) as gap_count FROM ordered
            WHERE next_ts IS NOT NULL AND next_ts > ts + INTERVAL '2 minutes'
            GROUP BY symbol
            """
            gaps_df = self.query(gaps_sql)
            gaps = int(gaps_df['gap_count'].sum()) if not gaps_df.empty else 0
            rowcount = int(self.query(f"SELECT COUNT(*) as c FROM {table}").iloc[0, 0])
            return {"rows": rowcount, "duplicates": dups, "gaps": gaps, "ok": dups == 0 and gaps == 0}
        except Exception as e:
            return {"error": str(e), "ok": False}

    def write_parquet(self, df: pd.DataFrame, name: str, partition_cols: list[str] | None = None) -> Path:
        p = self.base_dir / f"{name}.parquet"
        if partition_cols:
            # simple write, full partitioned would use dir
            df.to_parquet(p, index=False)
        else:
            df.to_parquet(p, index=False)
        return p
