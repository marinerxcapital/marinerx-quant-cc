"""Object storage abstraction — local filesystem (dev) and Cloudflare R2 (production)."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from mcc.core.config import MCCSettings, get_settings
from mcc.core.exceptions import ConfigError

logger = structlog.get_logger(__name__)

_SAFE_KEY_RE = re.compile(r"[^a-zA-Z0-9._/-]+")


def sanitize_object_key(key: str) -> str:
    cleaned = key.strip().lstrip("/")
    cleaned = _SAFE_KEY_RE.sub("_", cleaned)
    return cleaned


def build_report_key(report_id: str, ext: str, *, now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    return sanitize_object_key(f"reports/{ts.year:04d}/{ts.month:02d}/{ts.day:02d}/{report_id}.{ext}")


@dataclass
class StoredObject:
    key: str
    backend: str
    size_bytes: int
    uri: str


class ObjectStore(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError


class LocalObjectStore(ObjectStore):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = sanitize_object_key(key)
        return self.root / safe

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("object_store_put", backend="local", key=key, size=len(data), content_type=content_type)
        return StoredObject(key=key, backend="local", size_bytes=len(data), uri=str(path.resolve()))

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "backend": "local", "root": str(self.root.resolve())}


class R2ObjectStore(ObjectStore):
    def __init__(self, settings: MCCSettings) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise ConfigError(
                "boto3 is required for R2 storage. Install with: pip install -e '.[deploy]'",
                details={"error": str(exc)},
            ) from exc

        if not all([settings.r2_account_id, settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket_name]):
            raise ConfigError("R2 credentials incomplete", details={"backend": "r2"})

        endpoint = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
        self._bucket = settings.r2_bucket_name or ""
        self._public_base = (settings.r2_public_base_url or "").rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> StoredObject:
        safe_key = sanitize_object_key(key)
        self._client.put_object(Bucket=self._bucket, Key=safe_key, Body=data, ContentType=content_type)
        uri = f"{self._public_base}/{safe_key}" if self._public_base else f"s3://{self._bucket}/{safe_key}"
        logger.info("object_store_put", backend="r2", key=safe_key, size=len(data), content_type=content_type)
        return StoredObject(key=safe_key, backend="r2", size_bytes=len(data), uri=uri)

    def exists(self, key: str) -> bool:
        safe_key = sanitize_object_key(key)
        try:
            self._client.head_object(Bucket=self._bucket, Key=safe_key)
            return True
        except Exception:
            return False

    def health(self) -> dict[str, Any]:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return {"status": "ok", "backend": "r2", "bucket": self._bucket}
        except Exception as exc:
            return {"status": "error", "backend": "r2", "error": str(exc)}


def get_object_store(settings: MCCSettings | None = None) -> ObjectStore:
    cfg = settings or get_settings()
    if cfg.object_storage_backend == "r2":
        return R2ObjectStore(cfg)
    return LocalObjectStore(cfg.local_object_storage_dir)