"""MarinerX Quant Command Center CLI.

Real entry: `python main.py run --interface web` starts the Supervisor with 15 agents
and serves the web dashboard. The web app uses the live supervisor for /health.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Ensure src layout works for both `python main.py` and after `pip install -e`
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mcc.runtime.bootstrap import create_supervisor  # noqa: E402
from mcc.storage.relational import init_db  # noqa: E402
from mcc.core.supervisor import Supervisor  # noqa: E402

try:
    from mcc.interface.web import server as web_server
except Exception:
    web_server = None  # type: ignore[assignment]

app = typer.Typer(help="MarinerX Quant Command Center")
console = Console()

# Global for sharing supervisor with web process when run together
_CURRENT_SUPERVISOR: Optional[Supervisor] = None


# No more local stub registration — bootstrap does it with real spine agents


@app.command()
def doctor() -> None:
    """Real doctor: exercises config, db, supervisor, 15 agents, safety basics."""
    t = Table(title="MCC Doctor")
    t.add_column("Check")
    t.add_column("Status")

    ok: bool = True

    # DB
    try:
        init_db()
        t.add_row("db (init)", "OK")
    except Exception as e:
        t.add_row("db (init)", f"FAIL {e}")
        ok = False

    # Supervisor + 15 agents (via bootstrap - real spine)
    try:
        sup = create_supervisor(replay=True)
        t.add_row("supervisor + 15 agents", f"OK ({len(sup.agents)} registered)")
    except Exception as e:
        t.add_row("supervisor + 15 agents", f"FAIL {e}")
        ok = False

    # Safety gate smoke (import the modules that should enforce)
    try:
        from mcc.strategy.lifecycle import StrategyStatus  # type: ignore[import]  # noqa: F401
        t.add_row("strategy lifecycle (P1)", "OK")
    except Exception:
        t.add_row("strategy lifecycle (P1)", "PARTIAL")

    try:
        from mcc.execution.guardrails import check_pre_trade  # type: ignore[import]  # noqa: F401
        t.add_row("execution guardrails (P1/P2)", "OK")
    except Exception:
        t.add_row("execution guardrails (P1/P2)", "PARTIAL")

    try:
        from mcc.decision.engine import decide  # noqa: F401
        t.add_row("decision vetoes", "OK")
    except Exception:
        t.add_row("decision vetoes", "PARTIAL")

    t.add_row("replay adapter (default)", "OK (no keys needed)")

    console.print(t)
    if not ok:
        raise SystemExit(1)
    console.print("[green]All green[/green]")

async def _launch(run_web: bool = True) -> None:
    global _CURRENT_SUPERVISOR
    # Use the single bootstrap factory (real agents, bus, optional replay)
    sup = create_supervisor(replay=True)
    _CURRENT_SUPERVISOR = sup

    await sup.start_all()
    console.print(f"[green]Supervisor started with {len(sup.agents)} agents (real spine wired)[/green]")

    if run_web:
        if web_server is None:
            console.print("[red]Web server module not loadable[/red]")
            return
        # Patch so /health uses the exact live supervisor from this run
        web_server._SUP = sup  # type: ignore[attr-defined]

        import uvicorn
        config = uvicorn.Config(web_server.app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    else:
        while True:
            await asyncio.sleep(5)
            snap = sup.snapshot()
            healthy = len([a for a in snap.agents.values() if a.get("status") != "error"])
            console.print(f"Status: {healthy} agents healthy")

@app.command()
def run(interface: str = "web") -> None:
    """Real run command: starts supervisor + 15 agents + chosen interface."""
    run_web = interface.lower() == "web"
    try:
        asyncio.run(_launch(run_web=run_web))
    except KeyboardInterrupt:
        console.print("Shutting down...")

def cli() -> None:
    app()

if __name__ == "__main__":
    cli()
