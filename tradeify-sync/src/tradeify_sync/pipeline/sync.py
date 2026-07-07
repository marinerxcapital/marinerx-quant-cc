"""Main sync orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

from tradeify_sync.auth.login import ensure_authenticated
from tradeify_sync.browser.manager import BrowserManager
from tradeify_sync.config import Secrets, Settings, load_selectors
from tradeify_sync.constants import AuthError
from tradeify_sync.models import SyncRun, SyncStatus
from tradeify_sync.normalize.mapper import to_account, to_trade
from tradeify_sync.scrapers.accounts import AccountsScraper
from tradeify_sync.scrapers.fixtures import scrape_accounts_fixture, scrape_trades_fixture
from tradeify_sync.scrapers.trades import TradesScraper
from tradeify_sync.storage.db import session_scope
from tradeify_sync.storage.repository import (
    close_sync_run,
    insert_ignore_trades,
    last_trade_exit_utc,
    open_sync_run,
    upsert_account,
)
from tradeify_sync.utils.logging import get_logger, new_run_id

logger = get_logger(__name__)


async def run_sync(
    settings: Settings,
    secrets: Secrets,
    *,
    fixture_mode: bool = False,
    backfill_days: int | None = None,
) -> SyncRun:
    """Execute a full read-only sync."""
    run_id = new_run_id()
    run = SyncRun(run_id=run_id, started_utc=datetime.now(UTC))
    backfill = backfill_days or settings.sync.backfill_days_on_first_run
    display_tz = settings.sync.timezone_display

    try:
        with session_scope(settings) as session:
            run = open_sync_run(session, run_id)

            if fixture_mode:
                await _sync_fixtures(session, settings, run, backfill, display_tz)
            else:
                await _sync_live(session, settings, secrets, run, backfill, display_tz)

            run.finished_utc = datetime.now(UTC)
            close_sync_run(session, run)

    except AuthError as exc:
        run.status = SyncStatus.FAILED
        run.errors.append(str(exc))
        run.finished_utc = datetime.now(UTC)
        logger.error("sync_auth_failed", error=str(exc))
        with session_scope(settings) as session:
            close_sync_run(session, run)

    return run


async def _sync_fixtures(
    session: object,
    settings: Settings,
    run: SyncRun,
    backfill: int,
    display_tz: str,
) -> None:
    """Sync using HTML fixtures (CI mode)."""
    raw_accounts = scrape_accounts_fixture(settings)
    accounts = [to_account(r) for r in raw_accounts if r.get("account_id")]
    for acct in accounts:
        upsert_account(session, acct)  # type: ignore[arg-type]
    run.accounts_synced = len(accounts)

    for acct in accounts:
        raw_trades = scrape_trades_fixture(settings, acct.account_id)
        trades = [to_trade(r, acct.account_id, display_tz) for r in raw_trades]
        new_count = insert_ignore_trades(session, trades)  # type: ignore[arg-type]
        run.trades_new += new_count

    logger.info("fixture_sync_complete", accounts=len(accounts), trades_new=run.trades_new)


async def _sync_live(
    session: object,
    settings: Settings,
    secrets: Secrets,
    run: SyncRun,
    backfill: int,
    display_tz: str,
) -> None:
    """Sync using live browser."""
    selectors = load_selectors(settings.selectors_path)

    async with BrowserManager(settings) as bm:
        await ensure_authenticated(bm, settings, secrets)

        acct_scraper = AccountsScraper(bm.page, settings, selectors)
        raw_accounts = await acct_scraper.scrape_accounts()
        accounts = [to_account(r) for r in raw_accounts if r.get("account_id")]
        for acct in accounts:
            upsert_account(session, acct)  # type: ignore[arg-type]
        run.accounts_synced = len(accounts)

        trade_scraper = TradesScraper(bm.page, settings, selectors)
        for acct in accounts:
            try:
                since = last_trade_exit_utc(session, acct.account_id)  # type: ignore[arg-type]
                result = await trade_scraper.scrape_trades(acct.account_id, since, backfill)
                if "rows" in result:
                    trades = [to_trade(r, acct.account_id, display_tz) for r in result["rows"]]
                    new_count = insert_ignore_trades(session, trades)  # type: ignore[arg-type]
                    run.trades_new += new_count
            except Exception as exc:
                run.status = SyncStatus.PARTIAL
                run.errors.append(f"{acct.account_id}: {exc}")
                logger.error("account_sync_failed", account_id=acct.account_id, error=str(exc))