# Cloudflare R2 Storage

Object storage abstraction: local filesystem for development, Cloudflare R2 for production.

**Implementation:** `src/mcc/storage/object_store.py`  
**Config:** `OBJECT_STORAGE_BACKEND` and `R2_*` env vars in `src/mcc/core/config.py`

## Modes

| Mode | `OBJECT_STORAGE_BACKEND` | Backend class | Use case |
|------|--------------------------|---------------|----------|
| Local | `local` (default) | `LocalObjectStore` | Dev, CI, offline |
| Production | `r2` | `R2ObjectStore` | Render web + worker |

`get_object_store()` selects the backend at runtime. Production with `r2` validates credentials via `validate_production_requirements()`.

## Cloudflare R2 setup

1. **Create bucket** in Cloudflare dashboard → R2.
2. **Create API token** with Object Read & Write on that bucket.
3. Note your **Account ID** (dashboard URL or R2 overview).
4. Optionally attach a **custom domain** or R2.dev public URL for reads.

Set in Render (both services):

```env
OBJECT_STORAGE_BACKEND=r2
R2_ACCOUNT_ID=<account_id>
R2_ACCESS_KEY_ID=<access_key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=marinerx-mcc-prod
R2_PUBLIC_BASE_URL=https://assets.yourdomain.com   # optional but recommended
```

## Dependency

R2 requires `boto3` (S3-compatible API):

```bash
pip install -e ".[deploy]"
```

`R2ObjectStore` uses endpoint:

```
https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com
```

Region is set to `auto` per Cloudflare R2 convention.

## Key naming

All keys pass through `sanitize_object_key()`:

- Leading slashes stripped
- Unsafe characters replaced with `_` (allowed: `a-zA-Z0-9._/-`)

**Report keys** use `build_report_key()`:

```
reports/{YYYY}/{MM}/{DD}/{report_id}.{ext}
```

Example: `reports/2026/07/05/abc123.pdf`

Store metadata in Postgres `report_metadata.object_key` alongside `storage_backend` (`local` or `r2`).

## API surface

| Method | Behavior |
|--------|----------|
| `put_bytes(key, data, content_type=...)` | Write object; returns `StoredObject` with `uri` |
| `exists(key)` | Head/check presence |
| `health()` | Local: checks root dir; R2: `head_bucket` |

## URI formats

- **Local:** `file://` absolute path under `LOCAL_OBJECT_STORAGE_DIR`
- **R2 with public base:** `{R2_PUBLIC_BASE_URL}/{key}`
- **R2 without public base:** `s3://{bucket}/{key}`

## Local development

```env
OBJECT_STORAGE_BACKEND=local
LOCAL_OBJECT_STORAGE_DIR=./data/objects
```

Files are written to `{LOCAL_OBJECT_STORAGE_DIR}/{sanitized_key}` with parent dirs created automatically.

## Health check integration

`/health` includes:

```json
"object_storage": {"status": "ok", "backend": "r2", "bucket": "marinerx-mcc-prod"}
```

Errors surface as `"status": "error"` with `"error"` message — overall health becomes `error` or `degraded`.

## Security

- Use scoped R2 API tokens (bucket-specific).
- Prefer custom domain + Cloudflare access rules over wide-open public buckets.
- Do not commit credentials; Render `sync: false` for all `R2_*` keys in `render.yaml`.

## Verification

```bash
python -m pytest tests/deployment/test_object_store.py -q
python main.py doctor
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `boto3 is required` | `pip install -e ".[deploy]"` |
| `R2 credentials incomplete` | Set all four required `R2_*` vars |
| `head_bucket` fails | Check token permissions and bucket name |
| Wrong public URL | Verify `R2_PUBLIC_BASE_URL` has no trailing slash issues (code strips trailing `/`) |