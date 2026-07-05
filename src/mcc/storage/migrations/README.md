# Database Migrations

MarinerX uses **idempotent SQLAlchemy `create_all`** via `mcc.storage.database.init_db()`.

## Current approach

- Schema is defined in `src/mcc/storage/models.py`
- `init_db()` creates missing tables on startup
- Safe for SQLite (local) and Postgres (production)

## Future Alembic migration

When schema changes become non-trivial, add Alembic revisions here. Until then, `create_all` is the conservative migration strategy documented in `docs/deployment/DATABASE_MIGRATION.md`.