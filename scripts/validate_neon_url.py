"""Validate DATABASE_URL parses and connects (used by fix_render_deploy.ps1)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcc.core.config import MCCSettings, reset_settings_cache
from mcc.storage.database import check_database_connectivity, reset_engine


def main() -> int:
    reset_settings_cache()
    reset_engine()
    settings = MCCSettings(_env_file=None)
    url = settings.sqlalchemy_url
    if not url.startswith("postgresql"):
        print(f"FAIL: expected postgresql URL, got: {url[:40]}...")
        return 1
    print(f"SQLAlchemy URL scheme OK: {url.split('://', 1)[0]}")
    result = check_database_connectivity()
    print(f"Neon connectivity: {result}")
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())