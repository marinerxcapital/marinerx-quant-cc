# Railway Fallback Plan

Railway remains the **current production host** during migration to Render + Cloudflare + Postgres + R2.

## Current state

| Item | Value |
|------|-------|
| Production URL | https://marinerx-quant-cc-production.up.railway.app/ |
| Config file | `railway.json` (repo root — **kept intentionally**) |
| Docker | Same `Dockerfile` as Render target |
| Start command | `python main.py run --interface web` |
| Health | `GET /health` (Docker HEALTHCHECK + app endpoint) |

## railway.json

```json
{
  "build": { "builder": "DOCKERFILE" },
  "deploy": {
    "startCommand": "python main.py run --interface web",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```

No worker service on Railway today — worker is Render-only in `render.yaml`.

## Why keep Railway

1. **Proven production** — Phase 15 UI deployed and reachable
2. **Instant rollback** — revert DNS or traffic to Railway URL
3. **Parallel validation** — smoke-test Render before cutover
4. **Zero code divergence** — same Docker image and entrypoint

## Migration traffic strategy

```
Phase 1 (now):     Railway = primary production
Phase 2:           Render web + worker + Postgres + R2 = staging
Phase 3:           DNS cutover → Render primary
Phase 4:           Railway = standby (keep deployed 30 days)
Phase 5:           Decommission Railway after Render soak
```

## Rollback procedure

If Render deploy fails post-cutover:

1. Point DNS back to Railway hostname (or share staging URL).
2. Confirm https://marinerx-quant-cc-production.up.railway.app/health returns `status: ok`.
3. Verify `live_execution_enabled: false`.
4. Investigate Render logs; fix; redeploy.

**RTO target:** < 15 minutes (DNS TTL dependent).

## Environment differences

| Aspect | Railway (current) | Render (target) |
|--------|-------------------|-----------------|
| Web service | ✓ | `marinerx-labs-api` |
| Worker | ✗ | `marinerx-labs-worker` |
| Postgres | Likely ephemeral / none | Neon or Supabase via `DATABASE_URL` |
| Object storage | Local/ephemeral disk | Cloudflare R2 |
| Blueprint | `railway.json` | `render.yaml` |

After migration, Railway should **not** be relied on for durable data unless `DATABASE_URL` and R2 are also configured there.

## Cloud runtime detection

Railway sets `RAILWAY_ENVIRONMENT` / `RAILWAY_PROJECT_ID` — triggers:

- `is_cloud_runtime()` → true
- Tradeify automation blocked
- Production path expectations if `APP_ENV=production`

## Keeping Railway warm

- Leave GitHub → Railway auto-deploy enabled on `master`
- Push migration commits — Railway rebuilds with new config layer (backward compatible web mode)
- Do not delete `railway.json` or `Dockerfile`

## Verification

```bash
curl -s https://marinerx-quant-cc-production.up.railway.app/health
```

Expected: HTTP 200, JSON with `service_mode`, `agents`, `live_execution_enabled: false`.

## Decommission criteria

Safe to remove Railway when **all** are true for 30+ days:

- [ ] Render web stable, health green
- [ ] Render worker heartbeats in Postgres
- [ ] DNS points to Render/Cloudflare
- [ ] R2 objects serving reports
- [ ] No production incidents requiring Railway rollback
- [ ] Stakeholder sign-off

Until then: **keep Railway deployed and documented as fallback.**