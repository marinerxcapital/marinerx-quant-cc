# Database Migration

MarinerX uses a **dual-backend** database strategy: SQLite locally, managed Postgres in production.

## Architecture

| Environment | Backend | Connection |
|-------------|---------|------------|
| Local dev | SQLite | `sqlite:///{DATA_DIR}/mcc.sqlite` (default when `DATABASE_URL` unset) |
| Production / staging | Postgres | `DATABASE_URL` (Neon, Supabase, or other managed Postgres) |

Configuration: `src/mcc/core/config.py` → `MCCSettings.sqlalchemy_url`  
Engine & init: `src/mcc/storage/database.py`  
Models: `src/mcc/storage/models.py`

## Idempotent schema initialization

Schema is created with **SQLAlchemy `Base.metadata.create_all()`** on every engine creation. This is intentional and safe:

- Missing tables are created
- Existing tables are **not** altered or dropped
- Callable via `init_db()` or `get_engine()` — both invoke `create_all`

```python
# src/mcc/storage/database.py
eng = create_engine(db_url, ...)
Base.metadata.create_all(eng)
```

Startup path (`main.py`):

1. `validate_production_requirements()`
2. `init_db()` — creates schema before supervisor/agents start

## Tables

| Table | Purpose |
|-------|---------|
| `strategies` | Strategy registry and status |
| `account_states` | Equity/cash/PnL snapshots |
| `trades` | Trade ledger |
| `decision_logs` | Decision engine audit trail |
| `report_metadata` | Report object keys + storage backend |
| `agent_heartbeats` | Worker liveness records |

## Local setup

```bash
cp .env.example .env
# Leave DATABASE_URL commented out
python main.py doctor   # creates ./data/mcc.sqlite
```

SQLite file location: `{DATA_DIR}/mcc.sqlite` (default `./data/mcc.sqlite`).

SQLite engine uses `check_same_thread=False` for FastAPI/async compatibility.

## Production setup (Neon / Supabase)

1. Create a Postgres database in Neon or Supabase.
2. Copy the connection string (must use `postgresql://` or `postgresql+psycopg2://`).
3. Set `DATABASE_URL` in Render (web + worker services).
4. Set `APP_ENV=production`.

Example:

```env
APP_ENV=production
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/mcc?sslmode=require
```

Pool settings (Postgres only):

```env
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
```

Both web and worker services **must share the same `DATABASE_URL`** so heartbeats and relational state are consistent.

## Connectivity check

`check_database_connectivity()` runs `SELECT 1` and returns:

```json
{"status": "ok", "backend": "postgres", "url_scheme": "postgresql"}
```

Used by `/health` and `python main.py doctor`.

## Migration strategy (current vs future)

**Current (implemented):** Idempotent `create_all` — documented in `src/mcc/storage/migrations/README.md`.

**Future:** When schema changes require ALTER TABLE, data backfills, or destructive changes, add Alembic revisions under `src/mcc/storage/migrations/`. Until then, `create_all` is the conservative default.

## Operational notes

- **No manual migration CLI** — schema sync happens at process start.
- **Ephemeral disk on Render** — do not rely on SQLite in production; always set `DATABASE_URL`.
- **Worker heartbeats** accumulate in `agent_heartbeats`; plan retention/cleanup if volume grows.
- Reset local DB: delete `./data/mcc.sqlite` and restart — tables are recreated.

## Verification

```bash
# Local
python main.py doctor

# After setting DATABASE_URL
python -c "from mcc.storage.database import init_db, check_database_connectivity; init_db(); print(check_database_connectivity())"
```

## Rollback

- Schema changes via `create_all` are additive only (new tables).
- To roll back application code, redeploy previous image; existing Postgres data is preserved.
- For destructive schema changes (future Alembic), follow revision `downgrade()` procedures.