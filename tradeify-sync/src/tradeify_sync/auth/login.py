"""Login and 2FA handling."""

from __future__ import annotations

import asyncio

import pyotp

from tradeify_sync.auth.session import is_session_valid, session_state_path
from tradeify_sync.browser.guards import assert_navigable, guarded_click
from tradeify_sync.browser.humanize import human_pause
from tradeify_sync.browser.manager import BrowserManager
from tradeify_sync.config import Secrets, Settings, load_selectors
from tradeify_sync.constants import AuthError
from tradeify_sync.utils.logging import get_logger

logger = get_logger(__name__)

TWOFA_MANUAL_MESSAGE = """
================================================================================
  MANUAL 2FA REQUIRED
================================================================================
  Tradeify requires two-factor authentication. Complete the following steps:

  1. A headed browser window is open showing the Tradeify login/2FA page.
  2. Enter your 2FA code from your authenticator app (or approve the push).
  3. Complete any CAPTCHA or security challenge if prompted.
  4. Wait until you see the Tradeify dashboard.

  This process will continue automatically once the dashboard loads.
  (Set TRADEIFY_TOTP_SECRET in .env to automate TOTP codes.)
================================================================================
"""


async def _resolve_selector(page: object, selector: str) -> object:
    return page.locator(selector).first  # type: ignore[union-attr]


async def ensure_authenticated(
    bm: BrowserManager,
    settings: Settings,
    secrets: Secrets,
) -> None:
    """Ensure a valid authenticated session exists."""
    if await is_session_valid(bm, settings):
        return

    selectors = load_selectors(settings.selectors_path)
    login_sel = selectors.get("login", {})
    login_url = settings.page_url("login")
    assert_navigable(login_url, settings.tradeify.base_url)
    page = bm.page

    await page.goto(login_url, wait_until="domcontentloaded")
    await human_pause(settings)

    user_sel = login_sel.get("username_input", {}).get("primary", "input[type='email']")
    pass_sel = login_sel.get("password_input", {}).get("primary", "input[type='password']")
    submit_sel = login_sel.get("submit_button", {}).get("primary", "button[type='submit']")
    twofa_sel = login_sel.get("twofa_input", {}).get("primary", "")
    marker_sel = login_sel.get("logged_in_marker", {}).get("primary", "")

    if not secrets.tradeify_username or not secrets.tradeify_password:
        if settings.browser.headless:
            raise AuthError("Credentials missing; run `login` in headed mode first")
        print(TWOFA_MANUAL_MESSAGE)
        print("  No credentials in .env — complete login manually in the browser.")
        await _wait_for_marker(page, marker_sel, settings.browser.timeout_ms * 4)
        return

    await (await _resolve_selector(page, user_sel)).fill(secrets.tradeify_username)
    await (await _resolve_selector(page, pass_sel)).fill(secrets.tradeify_password)
    await guarded_click(page, await _resolve_selector(page, submit_sel))
    await human_pause(settings)

    twofa_locator = page.locator(twofa_sel).first if twofa_sel else None
    needs_2fa = False
    if twofa_locator:
        try:
            await twofa_locator.wait_for(state="visible", timeout=5000)
            needs_2fa = True
        except Exception:
            needs_2fa = False

    if needs_2fa:
        if secrets.tradeify_totp_secret:
            code = pyotp.TOTP(secrets.tradeify_totp_secret).now()
            await twofa_locator.fill(code)
            await guarded_click(page, await _resolve_selector(page, submit_sel))
        elif settings.browser.headless:
            raise AuthError("2FA requires headed mode; run `login` first")
        else:
            print(TWOFA_MANUAL_MESSAGE)
            await _wait_for_marker(page, marker_sel, settings.browser.timeout_ms * 4)

    try:
        await _wait_for_marker(page, marker_sel, settings.browser.timeout_ms)
    except AuthError:
        raise AuthError("Login failed — check credentials or complete 2FA") from None

    logger.info("login_success", session_path=str(session_state_path(settings)))


async def _wait_for_marker(page: object, marker_sel: str, timeout_ms: int) -> None:
    if not marker_sel:
        await asyncio.sleep(2)
        return
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while asyncio.get_event_loop().time() < deadline:
        try:
            loc = page.locator(marker_sel).first  # type: ignore[union-attr]
            if await loc.is_visible():
                return
        except Exception:
            pass
        await asyncio.sleep(1.0)
    raise AuthError("Timed out waiting for logged-in marker")