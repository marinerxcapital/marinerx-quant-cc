import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mcc.core.config import MCCSettings
from mcc.storage.object_store import LocalObjectStore, build_report_key, sanitize_object_key


def test_sanitize_object_key():
    assert sanitize_object_key("reports/2026/07/04/report.pdf") == "reports/2026/07/04/report.pdf"
    assert " " not in sanitize_object_key("bad key/with spaces")


def test_local_object_store_roundtrip(tmp_path):
    store = LocalObjectStore(tmp_path / "objects")
    key = build_report_key("abc123", "pdf")
    payload = b"%PDF-1.4 test"
    stored = store.put_bytes(key, payload, content_type="application/pdf")
    assert stored.backend == "local"
    assert store.exists(key)
    assert store.health()["status"] == "ok"


def test_r2_requires_credentials():
    settings = MCCSettings(
        _env_file=None,
        OBJECT_STORAGE_BACKEND="r2",
        R2_ACCOUNT_ID=None,
    )
    from mcc.storage.object_store import get_object_store

    try:
        get_object_store(settings)
        assert False, "expected ConfigError"
    except Exception as exc:
        assert "R2" in str(exc) or "credentials" in str(exc).lower()