#!/usr/bin/env python3
"""Tradeify Sync Engine CLI."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
import yaml

# Ensure src is on path when running as script
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tradeify_sync.auth.login import TWOFA_MANUAL_MESSAGE, ensure_authenticated
from tradeify_sync.auth.session import has_session
from tradeify_sync.browser.manager import BrowserManager
from tradeify_sync.config import Settings, get_settings, load_selectors
from tradeify_sync.constants import ConfigError
from tradeify_sync.models import Account, Fill, PayoutRecord, Trade
from tradeify_sync.pipeline.sync import run_sync
from tradeify_sync.storage.db import init_db, session_scope
from tradeify_sync.storage.repository import account_headroom, count_rows, get_last_sync_run, list_accounts
from tradeify_sync.utils.logging import configure_logging, get_logger

app = typer.Typer(help="Tradeify Sync Engine — read-only dashboard sync")
logger = get_logger(__name__)

MODEL_FIELDS = {
    "accounts": set(Account.model_fields.keys()),
    "trades": set(Trade.model_fields.keys()),
    "fills": set(Fill.model_fields.keys()),
    "payouts": set(PayoutRecord.model_fields.keys()),
}


def _load() -> Settings:
    settings = get_settings()
    configure_logging(
        level=settings.logging.level,
        json_output=settings.logging.json_output,
        log_dir=settings.logging.dir,
    )
    return settings


@app.command()
def doctor() -> None:
    """Validate configuration, session, selectors, and database."""
    checks: list[tuple[str, bool, str]] = []
    try:
        settings = Settings.load()
        checks.append(("config.yaml", True, "Valid"))
    except ConfigError as exc:
        typer.echo(f"Config error: {exc}")
        raise typer.Exit(1) from exc

    env_path = settings.project_root / ".env"
    checks.append((".env present", env_path.exists(), str(env_path)))

    checks.append(("session file", has_session(settings), settings.browser.session_path))

    try:
        selectors = load_selectors(settings.selectors_path)
        checks.append(("selectors.yaml", True, "Parses OK"))
        for page, fields in MODEL_FIELDS.items():
            col_map = selectors.get(page, {}).get("column_map", {})
            for field in col_map:
                ok = field in fields or field.replace("_time", "_time_utc") in fields
                if field in ("entry_time", "exit_time", "request_date", "processed_date"):
                    ok = True
                checks.append((f"  {page}.{field}", ok, "maps to model" if ok else "UNKNOWN FIELD"))
    except Exception as exc:
        checks.append(("selectors.yaml", False, str(exc)))

    try:
        init_db(settings)
        checks.append(("database", True, settings.storage.sqlite_path))
    except Exception as exc:
        checks.append(("database", False, str(exc)))

    typer.echo("\nTradeify Sync Doctor\n" + "=" * 50)
    all_ok = True
    for name, ok, detail in checks:
        status = typer.style("PASS", fg="green") if ok else typer.style("FAIL", fg="red")
        typer.echo(f"  [{status}] {name}: {detail}")
        if not ok:
            all_ok = False

    if not all_ok:
        raise typer.Exit(1)


@app.command()
def login() -> None:
    """Establish or refresh persisted browser session (headed, supports manual 2FA)."""
    settings = _load()
    settings.browser.headless = False
    typer.echo(TWOFA_MANUAL_MESSAGE)

    async def _do_login() -> None:
        async with BrowserManager(settings) as bm:
            await ensure_authenticated(bm, settings, settings.secrets)
        typer.echo("Session persisted to data/sessions/storage_state.json")

    asyncio.run(_do_login())


@app.command()
def discover(
    page: str | None = typer.Option(None, "--page", help="Discover a single page"),
) -> None:
    """Guided selector discovery (headed browser, manual 2FA)."""
    settings = _load()
    settings.browser.headless = False
    pages = [page] if page else ["accounts", "trades", "positions", "payouts"]

    typer.echo(TWOFA_MANUAL_MESSAGE)
    typer.echo("\nDiscovery mode: navigate to each page and press Enter to capture selectors.\n")

    async def _discover() -> None:
        selectors = load_selectors(settings.selectors_path)
        async with BrowserManager(settings) as bm:
            await ensure_authenticated(bm, settings, settings.secrets)
            for pg in pages:
                typer.echo(f"\n>>> Navigate to your **{pg}** page, then press Enter.")
                input()
                url = bm.page.url
                typer.echo(f"  Captured URL: {url}")
                selectors.setdefault(pg, {})
                selectors[pg]["discovered_url"] = url
                typer.echo(f"  Page '{pg}' recorded. Re-run with --page {pg} to update.")

        out = settings.selectors_path
        with out.open("w", encoding="utf-8") as fh:
            yaml.dump(selectors, fh, default_flow_style=False, sort_keys=False)
        typer.echo(f"\nWrote {out}")

    asyncio.run(_discover())


@app.command()
def sync(
    fixture: bool = typer.Option(False, "--fixture", help="Use HTML fixtures (CI mode)"),
) -> None:
    """Run a full read-only sync."""
    settings = _load()
    init_db(settings)

    async def _do_sync() -> None:
        result = await run_sync(settings, settings.secrets, fixture_mode=fixture)
        typer.echo(f"\nSync complete: {result.status.value}")
        typer.echo(f"  run_id:          {result.run_id}")
        typer.echo(f"  accounts_synced: {result.accounts_synced}")
        typer.echo(f"  trades_new:      {result.trades_new}")
        typer.echo(f"  fills_new:       {result.fills_new}")
        if result.errors:
            typer.echo(f"  errors:          {result.errors}")

    asyncio.run(_do_sync())


@app.command()
def status() -> None:
    """Show last sync run and per-account headroom."""
    settings = _load()
    init_db(settings)

    with session_scope(settings) as session:
        last = get_last_sync_run(session)
        accounts = list_accounts(session)
        account_summary = [
            (a.account_id, a.equity, account_headroom(session, a.account_id)) for a in accounts
        ]
        row_counts = {
            table: count_rows(session, table)
            for table in ("accounts", "trades", "fills", "positions", "payouts")
        }

    typer.echo("\nTradeify Sync Status\n" + "=" * 50)
    if last:
        typer.echo(f"Last run: {last.run_id} ({last.status.value})")
        typer.echo(f"  started:  {last.started_utc}")
        typer.echo(f"  trades_new: {last.trades_new}")
    else:
        typer.echo("No sync runs yet.")

    typer.echo("\nAccounts:")
    for account_id, equity, headroom in account_summary:
        typer.echo(f"  {account_id}: headroom={headroom}, equity={equity}")

    typer.echo("\nRow counts:")
    for table, count in row_counts.items():
        typer.echo(f"  {table}: {count}")


@app.command()
def export(
    fmt: str = typer.Option("parquet", "--fmt", help="parquet or csv"),
    table: str | None = typer.Option(None, "--table", help="Table name for csv export"),
) -> None:
    """Export database snapshots."""
    settings = _load()
    init_db(settings)
    out_dir = settings.resolve(settings.storage.parquet_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "parquet":
        try:
            import pandas as pd
            from sqlalchemy import create_engine

            engine = create_engine(f"sqlite:///{settings.resolve(settings.storage.sqlite_path)}")
            for tbl in ("accounts", "trades", "payouts", "positions"):
                df = pd.read_sql_table(tbl, engine)
                path = out_dir / f"{tbl}.parquet"
                df.to_parquet(path, index=False)
                typer.echo(f"Exported {path}")
        except Exception as exc:
            typer.echo(f"Export failed: {exc}")
            raise typer.Exit(1) from exc
    elif fmt == "csv" and table:
        try:
            import pandas as pd
            from sqlalchemy import create_engine

            engine = create_engine(f"sqlite:///{settings.resolve(settings.storage.sqlite_path)}")
            df = pd.read_sql_table(table, engine)
            path = out_dir / f"{table}.csv"
            df.to_csv(path, index=False)
            typer.echo(f"Exported {path}")
        except Exception as exc:
            typer.echo(f"Export failed: {exc}")
            raise typer.Exit(1) from exc
    else:
        typer.echo("Use --fmt parquet or --fmt csv --table <name>")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()