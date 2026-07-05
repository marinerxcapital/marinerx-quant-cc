"""Phase 17 — report generator Seaborn styling."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from mcc.reports.generator import apply_report_style, generate_line_chart, get_active_style


def test_apply_seaborn_style(tmp_path: Path):
    style = apply_report_style()
    assert "seaborn" in style.lower() or style == "seaborn-whitegrid"
    assert get_active_style() != "matplotlib-default"


def test_generate_line_chart_png(tmp_path: Path):
    series = pd.Series([1.0, 2.0, 1.5, 3.0, 2.5])
    out = generate_line_chart(series, title="Phase 17 Evidence", output_path=tmp_path / "evidence.png")
    assert out.exists()
    assert out.stat().st_size > 500