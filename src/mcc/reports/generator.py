"""Report chart generation with Seaborn default styling (Phase 17)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import structlog

logger = structlog.get_logger(__name__)

_STYLE_APPLIED = False
_ACTIVE_STYLE = "seaborn-v0_8-whitegrid"


def apply_report_style() -> str:
    """Apply Seaborn as the default matplotlib style for static report charts."""
    global _STYLE_APPLIED, _ACTIVE_STYLE
    sns.set_theme(style="whitegrid", context="talk")
    _STYLE_APPLIED = True
    _ACTIVE_STYLE = "seaborn-whitegrid"
    logger.info("report_style_applied", style=_ACTIVE_STYLE)
    return _ACTIVE_STYLE


def get_active_style() -> str:
    """Return the active report style name."""
    return _ACTIVE_STYLE if _STYLE_APPLIED else "matplotlib-default"


def generate_line_chart(
    series: pd.Series | Sequence[float],
    *,
    title: str = "Report Chart",
    xlabel: str = "Index",
    ylabel: str = "Value",
    output_path: str | Path,
) -> Path:
    """Render a static PNG line chart using the Seaborn report style."""
    apply_report_style()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(series, pd.Series):
        y = series.values.astype(float)
    else:
        y = [float(v) for v in series]

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(x=list(range(len(y))), y=y, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info("report_chart_saved", path=str(out))
    return out


def export_trades_to_excel(
    trades: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Optional openpyxl export for trade logs (Phase 17 item 5)."""
    try:
        import openpyxl  # noqa: F401 — optional dependency
    except ImportError as exc:
        raise ImportError("openpyxl required for Excel export: pip install openpyxl") from exc

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(trades)
    df.to_excel(out, index=False, engine="openpyxl")
    logger.info("trades_excel_exported", path=str(out), rows=len(df))
    return out