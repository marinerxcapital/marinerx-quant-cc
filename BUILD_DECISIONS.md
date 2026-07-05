# BUILD DECISIONS LEDGER

## Phase 15 — UI Fidelity Match (2026-07-04)

- **Scope:** Frontend-only pass per `command-center/15_UI_MATCH_AND_RAILWAY_DEPLOY.md`. No backend/agent/risk/validation logic changes.
- **Design source:** Packaged PNG mockups + `MOCKUP_REFERENCE.md` + logo/X icon from `MarinerX_Labs_SuperGrok_UI_Match_Final_Package.zip`.
- **Architecture:** Single-page app with hash routing in `static/index.html`, `pages.js`, `app.js`, shared `design-tokens.css` + `app.css`.
- **Server change:** `server.py` root route serves `static/index.html` (fallback to legacy `_DASHBOARD_HTML`). `/health` and `/ws` unchanged.
- **Light theme:** Replaced Phase 14 dark Tailwind dashboard with institutional light theme per mockup spec.
- **Sample data:** Static mockup data in `pages.js` (not live backend feeds) — acceptable for UI fidelity gate.
- **Charts:** Plotly.js with white-background config matching mockup chart styling.
- **Deploy:** GitHub push to `marinerxcapital/marinerx-quant-cc` master triggers Railway auto-deploy.