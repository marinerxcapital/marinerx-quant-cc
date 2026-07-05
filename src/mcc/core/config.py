"""Centralized environment-driven configuration for local, staging, and production."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcc.core.exceptions import ConfigError

ServiceMode = Literal["web", "worker"]
ObjectStorageBackend = Literal["local", "r2"]
AppEnv = Literal["local", "development", "staging", "production"]


def _parse_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return default


def is_cloud_runtime() -> bool:
    """Detect common cloud host environment markers."""
    markers = (
        "RENDER",
        "RENDER_SERVICE_ID",
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PROJECT_ID",
        "CF_PAGES",
        "VERCEL",
        "FLY_APP_NAME",
    )
    return any(os.environ.get(k) for k in markers)


class MCCSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    service_mode: ServiceMode = Field(default="web", alias="SERVICE_MODE")

    public_frontend_url: str = Field(default="http://localhost:8000", alias="PUBLIC_FRONTEND_URL")
    backend_public_url: str = Field(default="http://localhost:8000", alias="BACKEND_PUBLIC_URL")
    websocket_public_url: str | None = Field(default=None, alias="WEBSOCKET_PUBLIC_URL")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    log_dir: Path = Field(default=Path("./data/logs"), alias="LOG_DIR")
    parquet_dir: Path = Field(default=Path("./data/parquet"), alias="PARQUET_DIR")
    reports_dir: Path = Field(default=Path("./data/reports"), alias="REPORTS_DIR")
    local_object_storage_dir: Path = Field(default=Path("./data/objects"), alias="LOCAL_OBJECT_STORAGE_DIR")

    object_storage_backend: ObjectStorageBackend = Field(default="local", alias="OBJECT_STORAGE_BACKEND")

    r2_account_id: str | None = Field(default=None, alias="R2_ACCOUNT_ID")
    r2_access_key_id: str | None = Field(default=None, alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = Field(default=None, alias="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str | None = Field(default=None, alias="R2_BUCKET_NAME")
    r2_public_base_url: str | None = Field(default=None, alias="R2_PUBLIC_BASE_URL")

    enable_live_execution: bool = Field(default=False, alias="ENABLE_LIVE_EXECUTION")
    cors_allowed_origins: str = Field(default="*", alias="CORS_ALLOWED_ORIGINS")

    structlog_level: str = Field(default="INFO", alias="STRUCTLOG_LEVEL")
    agent_heartbeat_interval_seconds: int = Field(default=30, alias="AGENT_HEARTBEAT_INTERVAL_SECONDS")
    worker_shutdown_timeout_seconds: int = Field(default=30, alias="WORKER_SHUTDOWN_TIMEOUT_SECONDS")
    healthcheck_timeout_seconds: int = Field(default=5, alias="HEALTHCHECK_TIMEOUT_SECONDS")

    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    @field_validator("enable_live_execution", mode="before")
    @classmethod
    def _validate_live_execution(cls, value: object) -> bool:
        return _parse_bool(value, default=False)

    @field_validator("data_dir", "log_dir", "parquet_dir", "reports_dir", "local_object_storage_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: object) -> Path:
        return Path(str(value)) if not isinstance(value, Path) else value

    @property
    def effective_port(self) -> int:
        return int(os.environ.get("PORT", str(self.app_port)))

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in ("production", "prod", "staging")

    @property
    def is_local(self) -> bool:
        return self.app_env.strip().lower() in ("local", "development", "dev")

    @staticmethod
    def normalize_database_url(url: str) -> str:
        """Use psycopg v3 driver when URL is plain postgresql:// (Neon default)."""
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.normalize_database_url(self.database_url)
        if self.is_production and not self.database_url:
            raise ConfigError(
                "DATABASE_URL is required when APP_ENV is production or staging",
                details={"app_env": self.app_env},
            )
        sqlite_path = self.data_dir / "mcc.sqlite"
        return f"sqlite:///{sqlite_path.resolve()}"

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.log_dir, self.parquet_dir, self.reports_dir, self.local_object_storage_dir):
            path.mkdir(parents=True, exist_ok=True)

    def validate_production_requirements(self) -> None:
        if not self.is_production:
            return
        _ = self.sqlalchemy_url
        if self.object_storage_backend == "r2":
            missing = [
                name
                for name, val in (
                    ("R2_ACCOUNT_ID", self.r2_account_id),
                    ("R2_ACCESS_KEY_ID", self.r2_access_key_id),
                    ("R2_SECRET_ACCESS_KEY", self.r2_secret_access_key),
                    ("R2_BUCKET_NAME", self.r2_bucket_name),
                )
                if not val
            ]
            if missing:
                raise ConfigError(
                    "R2 object storage selected but required variables are missing",
                    details={"missing": missing},
                )

    def cors_origin_list(self) -> list[str]:
        raw = self.cors_allowed_origins.strip()
        if raw == "*":
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]


@lru_cache
def get_settings() -> MCCSettings:
    settings = MCCSettings()
    if settings.is_production:
        settings.data_dir = Path(os.environ.get("DATA_DIR", "/data"))
        settings.log_dir = Path(os.environ.get("LOG_DIR", "/data/logs"))
        settings.parquet_dir = Path(os.environ.get("PARQUET_DIR", "/data/parquet"))
        settings.reports_dir = Path(os.environ.get("REPORTS_DIR", "/data/reports"))
        settings.local_object_storage_dir = Path(os.environ.get("LOCAL_OBJECT_STORAGE_DIR", "/data/objects"))
    settings.ensure_directories()
    return settings


def reset_settings_cache() -> None:
    get_settings.cache_clear()