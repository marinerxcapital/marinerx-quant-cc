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


async def _resolve_selector(page: object, selector: str, timeout_ms: int = 30000) -> object:
    loc = page.locator(selector).first  # type: ignore[union-attr]
    await loc.wait_for(state="visible", timeout=timeout_ms)
    return loc


async def _try_fill(page: object, selectors: list[str], value: str, timeout_ms: int) -> bool:
    per_selector = max(5000, timeout_ms // max(len(selectors), 1))
    for sel in selectors:
        if not sel:
            continue
        try:
            loc = page.locator(sel).first  # type: ignore[union-attr]
            await loc.wait_for(state="visible", timeout=per_selector)
            await loc.fill(value)
            return True
        except Exception:
            continue
    return False


def _login_field_selectors(login_sel: dict, field: str, defaults: list[str]) -> list[str]:
    block = login_sel.get(field, {})
    out: list[str] = []
    primary = block.get("primary", "")
    if primary:
        out.extend(s.strip() for s in primary.split(",") if s.strip())
    out.extend(block.get("fallbacks", []))
    out.extend(defaults)
    seen: set[str] = set()
    ordered: list[str] = []
    for sel in out:
        if sel not in seen:
            seen.add(sel)
            ordered.append(sel)
    return ordered


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

    await page.goto(login_url, wait_until="domcontentloaded", timeout=settings.browser.timeout_ms)
    await human_pause(settings)

    user_selectors = _login_field_selectors(
        login_sel,
        "username_input",
        ["input[type='email']", "input[name='email']", "input[autocomplete='username']", "input[type='text']"],
    )
    pass_selectors = _login_field_selectors(
        login_sel,
        "password_input",
        ["input[type='password']", "input[name='password']", "input[autocomplete='current-password']"],
    )
    submit_selectors = _login_field_selectors(
        login_sel,
        "submit_button",
        ["button[type='submit']", "button:has-text('Sign in')", "button:has-text('Log in')"],
    )
    twofa_sel = login_sel.get("twofa_input", {}).get("primary", "")
    marker_sel = login_sel.get("logged_in_marker", {}).get("primary", "")

    if not secrets.tradeify_username or not secrets.tradeify_password:
        if settings.browser.headless:
            raise AuthError("Credentials missing; run `login` in headed mode first")
        print(TWOFA_MANUAL_MESSAGE)
        print("  No credentials in .env — complete login manually in the browser.")
        await _wait_for_login_complete(page, marker_sel, settings.browser.timeout_ms * 4)
        return

    filled_user = await _try_fill(page, user_selectors, secrets.tradeify_username, settings.browser.timeout_ms)
    filled_pass = await _try_fill(page, pass_selectors, secrets.tradeify_password, settings.browser.timeout_ms)
    if not filled_user or not filled_pass:
        if settings.browser.headless:
            raise AuthError("Could not find login fields; run `login` in headed mode")
        print(TWOFA_MANUAL_MESSAGE)
        print("  Auto-fill could not find login fields — complete login manually in the browser.")
        await _wait_for_login_complete(page, marker_sel, settings.browser.timeout_ms * 4)
        return

    clicked = False
    for submit_sel in submit_selectors:
        try:
            await guarded_click(page, await _resolve_selector(page, submit_sel, 10000))
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        print(TWOFA_MANUAL_MESSAGE)
        print("  Could not click submit — press Sign in manually in the browser.")
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
            await _wait_for_login_complete(page, marker_sel, settings.browser.timeout_ms * 4)

    try:
        await _wait_for_login_complete(page, marker_sel, settings.browser.timeout_ms)
    except AuthError:
        raise AuthError("Login failed — check credentials or complete 2FA") from None

    logger.info("login_success", session_path=str(session_state_path(settings)))


_LOGIN_URL_MARKERS = ("/auth/login", "/login", "/signin", "/sign-in")


def _url_looks_logged_in(url: str) -> bool:
    lower = url.lower()
    return not any(marker in lower for marker in _LOGIN_URL_MARKERS)


async def _wait_for_login_complete(page: object, marker_sel: str, timeout_ms: int) -> None:
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while asyncio.get_event_loop().time() < deadline:
        try:
            current_url = page.url  # type: ignore[union-attr]
            if _url_looks_logged_in(current_url):
                return
        except Exception:
            pass
        if marker_sel:
            try:
                loc = page.locator(marker_sel).first  # type: ignore[union-attr]
                if await loc.is_visible():
                    return
            except Exception:
                pass
        await asyncio.sleep(1.0)
    raise AuthError("Timed out waiting for dashboard after login")