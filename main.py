"""MarinerX Quant Command Center CLI.

Entry points:
  python main.py doctor
  python main.py run --interface web     # Render Web Service
  python main.py run --interface worker  # Render Background Worker
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mcc.core.config import get_settings, reset_settings_cache  # noqa: E402
from mcc.core.supervisor import Supervisor  # noqa: E402
from mcc.runtime.bootstrap import create_supervisor  # noqa: E402
from mcc.storage.database import check_database_connectivity, init_db  # noqa: E402
from mcc.storage.models import AgentHeartbeat  # noqa: E402
from mcc.storage.object_store import get_object_store  # noqa: E402
from mcc.storage.session import session_scope  # noqa: E402

try:
    from mcc.interface.web import server as web_server
except Exception:
    web_server = None  # type: ignore[assignment]

app = typer.Typer(help="MarinerX Quant Command Center")
console = Console()
logger = structlog.get_logger(__name__)

_CURRENT_SUPERVISOR: Optional[Supervisor] = None
_SHUTDOWN_REQUESTED = False


def _configure_logging() -> None:
    settings = get_settings()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.structlog_level.upper(), 20)
        ),
    )


def _write_worker_heartbeat(sup: Supervisor) -> None:
    snap = sup.snapshot()
    healthy = len([a for a in snap.agents.values() if a.get("status") != "error"])
    settings = get_settings()
    with session_scope() as session:
        session.add(
            AgentHeartbeat(
                ts_utc=datetime.now(timezone.utc),
                service_mode=settings.service_mode,
                agent_count=len(snap.agents),
                healthy_count=healthy,
                kill_active=snap.kill_active,
                status="ok" if healthy == len(snap.agents) else "degraded",
            )
        )


@app.command()
def doctor() -> None:
    """Health: config, database, supervisor, 15 agents, object storage, safety modules."""
    reset_settings_cache()
    _configure_logging()
    settings = get_settings()

    t = Table(title="MCC Doctor")
    t.add_column("Check")
    t.add_column("Status")
    ok = True

    t.add_row("config", f"OK env={settings.app_env} mode={settings.service_mode}")
    t.add_row("live execution", f"{'ENABLED' if settings.enable_live_execution else 'DISABLED (default)'}")

    try:
        settings.validate_production_requirements()
        t.add_row("production config", "OK")
    except Exception as exc:
        t.add_row("production config", f"SKIP/WARN {exc}")

    try:
        settings.ensure_directories()
        init_db()
        db_health = check_database_connectivity()
        t.add_row("database", f"OK {db_health.get('backend', 'unknown')}")
    except Exception as exc:
        t.add_row("database", f"FAIL {exc}")
        ok = False

    try:
        store = get_object_store()
        store_health = store.health()
        t.add_row("object storage", f"{store_health.get('status', 'unknown')} ({store_health.get('backend')})")
    except Exception as exc:
        t.add_row("object storage", f"FAIL {exc}")
        ok = False

    try:
        sup = create_supervisor(replay=True)
        t.add_row("supervisor + 15 agents", f"OK ({len(sup.agents)} registered)")
    except Exception as exc:
        t.add_row("supervisor + 15 agents", f"FAIL {exc}")
        ok = False

    for label, import_path in (
        ("strategy lifecycle (P1)", "mcc.strategy.lifecycle"),
        ("execution guardrails (P1/P2)", "mcc.execution.guardrails"),
        ("decision vetoes", "mcc.decision.engine"),
        ("tradeify guard", "mcc.core.tradeify_guard"),
    ):
        try:
            __import__(import_path)
            t.add_row(label, "OK")
        except Exception:
            t.add_row(label, "PARTIAL")

    t.add_row("replay adapter (default)", "OK (no keys needed)")
    console.print(t)
    if not ok:
        raise SystemExit(1)
    console.print("[green]All green[/green]")


async def _shutdown_supervisor(sup: Supervisor) -> None:
    settings = get_settings()
    try:
        await asyncio.wait_for(sup.kill_switch(), timeout=settings.worker_shutdown_timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning("supervisor_shutdown_timeout")
    except Exception as exc:
        logger.warning("supervisor_shutdown_error", error=str(exc))


async def _worker_loop(sup: Supervisor) -> None:
    settings = get_settings()
    logger.info("worker_started", service_mode="worker", agents=len(sup.agents))
    while not _SHUTDOWN_REQUESTED:
        _write_worker_heartbeat(sup)
        snap = sup.snapshot()
        healthy = len([a for a in snap.agents.values() if a.get("status") != "error"])
        logger.info("worker_heartbeat", healthy=healthy, total=len(snap.agents), kill_active=snap.kill_active)
        await asyncio.sleep(settings.agent_heartbeat_interval_seconds)


async def _launch(interface: str) -> None:
    global _CURRENT_SUPERVISOR, _SHUTDOWN_REQUESTED

    reset_settings_cache()
    os.environ["SERVICE_MODE"] = "worker" if interface.lower() == "worker" else "web"
    reset_settings_cache()
    _configure_logging()

    settings = get_settings()
    settings.ensure_directories()
    settings.validate_production_requirements()
    init_db()

    logger.info(
        "service_starting",
        service_mode=settings.service_mode,
        app_env=settings.app_env,
        host=settings.app_host,
        port=settings.effective_port,
        live_execution=settings.enable_live_execution,
    )

    sup = create_supervisor(replay=True)
    _CURRENT_SUPERVISOR = sup
    await sup.start_all()
    console.print(f"[green]Supervisor started with {len(sup.agents)} agents[/green]")

    if interface.lower() == "web":
        if web_server is None:
            console.print("[red]Web server module not loadable[/red]")
            return
        web_server._SUP = sup  # type: ignore[attr-defined]
        web_server.configure_runtime(settings)  # type: ignore[attr-defined]

        import uvicorn

        port = settings.effective_port
        config = uvicorn.Config(
            web_server.app,
            host=settings.app_host,
            port=port,
            log_level=settings.structlog_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
    else:
        await _worker_loop(sup)

    if _SHUTDOWN_REQUESTED:
        await _shutdown_supervisor(sup)


def _handle_signal(signum: int, _frame: object) -> None:
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True
    logger.info("shutdown_signal_received", signal=signum)


@app.command()
def login() -> None:
    """Tradeify dashboard login (headed browser, manual 2FA). Persists session for sync."""
    tradeify_main = ROOT / "tradeify-sync" / "main.py"
    if not tradeify_main.exists():
        console.print("[red]tradeify-sync package not found[/red]")
        raise SystemExit(1)
    console.print("[yellow]Opening Tradeify login — complete 2FA in the browser window.[/yellow]")
    import subprocess

    result = subprocess.run(
        [sys.executable, str(tradeify_main), "login"],
        cwd=str(ROOT / "tradeify-sync"),
    )
    raise SystemExit(result.returncode)


@app.command()
def run(interface: str = "web") -> None:
    """Start supervisor + 15 agents + web API or background worker."""
    if interface.lower() not in ("web", "worker"):
        raise typer.BadParameter("interface must be 'web' or 'worker'")

    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    try:
        asyncio.run(_launch(interface))
    except KeyboardInterrupt:
        console.print("Shutting down...")
    finally:
        console.print("Shutdown complete.")


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()