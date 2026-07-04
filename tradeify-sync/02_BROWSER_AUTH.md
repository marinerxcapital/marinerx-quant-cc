# PHASE 02 — BROWSER · AUTH (read-only guards, session persistence, login/2FA)

**CONTEXT:** Phase 01 is complete (`config`, `constants` incl. allowlist/denylist and exceptions, `models`, `schema/db`, `logging`, `timeparse`). Now build the browser layer and authentication. This phase must make the READ-ONLY constraint (C1) structurally impossible to violate.

---

## 1. `src/tradeify_sync/browser/manager.py`
- `class BrowserManager` wrapping Playwright's async API.
- `async launch()` → persistent context via `chromium.launch_persistent_context` using a profile dir under `data/sessions/profile/`, honoring `browser.headless`, sane viewport, realistic user-agent, `accept_downloads=True`, download path `data/downloads/`.
- Load `storage_state.json` if present; expose `page` accessor.
- Register a **route/click interception hook** that funnels every navigation and click through `guards.py` (see §3).
- `async close()` persists `storage_state` back to disk.
- Context manager (`async with BrowserManager(settings) as bm:`).

## 2. `src/tradeify_sync/browser/humanize.py`
- `async human_pause(settings)` → sleep a uniform random ms in `[min_delay_ms, max_delay_ms]`.
- `async human_scroll(page)` and `async human_move(page, selector)` → small randomized scroll/cursor motions before interacting.
- Pure timing/UX; no data logic.

## 3. `src/tradeify_sync/browser/guards.py` — the safety core
- `assert_navigable(url)` → raise `NavigationError` unless `url` matches `URL_ALLOWLIST_PATTERNS`.
- `assert_non_mutating(element_descriptor)` → given an element's text + key attributes (`aria-label`, `name`, `id`, `value`, `type`), raise `MutatingInteractionBlocked` (subclass of `NavigationError`) if any token matches `MUTATING_INTERACTION_DENYLIST`.
- `guarded_click(page, locator)` → resolves the element's text/attrs, calls `assert_non_mutating`, then clicks. **All scraper clicks must route through `guarded_click`.**
- Emit a structured log on every allow/deny decision (selector key + decision, never full HTML).
- Design so this module is unit-testable without a live browser (accept plain descriptors).

## 4. `src/tradeify_sync/auth/session.py`
- `session_state_path(settings)`; `has_session()`.
- `async is_session_valid(bm, settings)` → navigate to dashboard root (allowlist-checked) and check for `login.logged_in_marker` from `selectors.yaml`; return bool. Never mutate.
- `async persist_session(bm)` / `async clear_session()`.

## 5. `src/tradeify_sync/auth/login.py`
- `async ensure_authenticated(bm, settings, secrets)`:
  1. If `is_session_valid` → return.
  2. Else navigate to `login_path`, resolve `login.username_input` / `password_input` via selector layer, fill from `secrets`, `guarded_click` submit.
  3. **2FA branch:** if a `login.twofa_input` appears: if `TRADEIFY_TOTP_SECRET` set → compute code with `pyotp` and submit; else enter **manual-assist mode**: if headed, print a clear terminal prompt and `await` until the `logged_in_marker` appears (poll with timeout) so the user completes 2FA/captcha by hand; if headless, raise `AuthError("2FA requires headed mode; run `login` first")`.
  4. On success, `persist_session`.
  5. On credential failure, raise `AuthError` (do **not** retry-hammer).
- Never log credentials or codes.

---

## PHASE 02 ACCEPTANCE GATE
- `test_guards.py` (write it now) proves: allowlisted URLs pass; a non-allowlisted URL raises `NavigationError`; descriptors containing `buy`/`sell`/`withdraw`/`reset`/`close position` raise `MutatingInteractionBlocked`; a benign `Next page` descriptor passes.
- `python main.py login` (temporary thin entry acceptable this phase) opens a headed browser, allows manual login, and persists a valid `storage_state.json`; a re-run detects the existing valid session without re-login.
- `ruff` + `mypy --strict src/` clean.

Deliver all Phase 02 files complete. Stop and await Phase 03.
