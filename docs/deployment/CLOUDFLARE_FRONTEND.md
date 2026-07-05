# Cloudflare Frontend Deployment

MarinerX supports two frontend deployment modes. **Mode A is active today**; Mode B is documented for a future extraction.

## Mode A — FastAPI static (current)

**Status:** Implemented and deployed.

The Phase 15 SPA is served directly by the FastAPI web service:

| Asset | Path |
|-------|------|
| Entry HTML | `src/mcc/interface/web/static/index.html` |
| App logic | `static/app.js`, `static/pages.js` |
| Styles | `static/app.css`, `static/design-tokens.css` |
| Mount | `/static/*` via `StaticFiles` |
| Root | `GET /` serves `index.html` |

**URLs in production:**

```env
PUBLIC_FRONTEND_URL=https://marinerx-labs-api.onrender.com
BACKEND_PUBLIC_URL=https://marinerx-labs-api.onrender.com
WEBSOCKET_PUBLIC_URL=wss://marinerx-labs-api.onrender.com/ws
```

**Cloudflare role (Mode A):**

- Optional: put Cloudflare proxy in front of Render origin (orange cloud)
- DNS `CNAME` → Render web service hostname
- SSL/TLS: Full (strict) with Render origin certificate
- No separate Pages project required

**Pros:** Single deploy unit, no CORS complexity, WebSocket same-origin.  
**Cons:** Static assets compete for web service resources; no global CDN edge cache for JS/CSS unless Cloudflare proxies the API domain.

## Mode B — Cloudflare Pages (future)

**Status:** Documented only — not required for current migration.

Extract static frontend to Cloudflare Pages; API remains on Render.

### Target architecture

```
User → Cloudflare Pages (static SPA)
     → Render API (REST + WebSocket)
     → Neon/Supabase (Postgres)
     → Cloudflare R2 (objects)
```

### Migration steps (when ready)

1. Create Cloudflare Pages project from `src/mcc/interface/web/static/` (or a thin build wrapper).
2. Set Pages env vars:
   - `VITE_API_URL` / `PUBLIC_API_URL` → Render `BACKEND_PUBLIC_URL`
   - `VITE_WS_URL` → Render `WEBSOCKET_PUBLIC_URL`
3. Update `app.js` to use env-based API base (today uses relative `/health`, `/ws`).
4. Set Render `CORS_ALLOWED_ORIGINS` to Pages domain (e.g. `https://app.marinerxlabs.com`).
5. Disable static serving on FastAPI root (optional) — API-only mode.
6. DNS: `app.` subdomain → Pages; `api.` subdomain → Render.

### Mode B checklist

- [ ] Refactor frontend API calls from relative to configurable base URL
- [ ] WebSocket URL configurable (wss://)
- [ ] CORS locked to Pages origin
- [ ] Cookie/auth strategy if added later
- [ ] E2E test against split origins

## CORS configuration

Mode A (same origin): `CORS_ALLOWED_ORIGINS=*` acceptable for initial deploy.

Mode B (split origin): **required** explicit origin:

```env
CORS_ALLOWED_ORIGINS=https://app.marinerxlabs.com
```

Configured in `server.py` via `settings.cors_origin_list()`.

## WebSocket

Dashboard uses `WS /ws` for live agent snapshots. Mode A: same host. Mode B: client must connect to `WEBSOCKET_PUBLIC_URL` on Render (ensure Cloudflare WebSocket support if proxying).

## Recommendation

1. **Now:** Deploy Mode A on Render; optionally front with Cloudflare DNS/proxy.
2. **Later:** Extract to Pages after backend is stable on Render + Postgres + R2.
3. **Do not block** Render migration waiting for Pages split.

## Related docs

- `RENDER_WEB_SERVICE.md` — API host
- `ENVIRONMENT_VARIABLES.md` — `PUBLIC_FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`
- `R2_STORAGE.md` — report/asset URLs via `R2_PUBLIC_BASE_URL`