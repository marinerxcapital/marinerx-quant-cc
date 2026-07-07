"""Configuration loading from YAML and environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from tradeify_sync.constants import ConfigError

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TradeifyConfig(BaseModel):
    """Tradeify dashboard connection settings."""

    base_url: str
    login_path: str = "/login"

    @field_validator("base_url")
    @classmethod
    def must_be_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("base_url must use HTTPS")
        return v.rstrip("/")


class BrowserConfig(BaseModel):
    """Playwright browser settings."""

    headless: bool = False
    persist_session: bool = True
    session_path: str = "data/sessions/storage_state.json"
    min_delay_ms: int = 800
    max_delay_ms: int = 2500
    timeout_ms: int = 30000


class SyncConfig(BaseModel):
    """Sync cadence and timezone settings."""

    cadence_minutes: int = 20
    market_hours_only: bool = True
    timezone_display: str = "America/New_York"
    timezone_store: str = "UTC"
    backfill_days_on_first_run: int = 90
    min_cadence_minutes: int = 5


class StorageConfig(BaseModel):
    """Local persistence paths."""

    sqlite_path: str = "data/tradeify_sync.db"
    parquet_dir: str = "data/parquet"
    export_after_each_sync: bool = True


class IntegrationConfig(BaseModel):
    """Optional remote read API (Railway hybrid)."""

    remote_read_api_enabled: bool = False


class InstrumentSpec(BaseModel):
    """Tick size and value for an instrument root."""

    tick_size: float
    tick_value: float


class LoggingConfig(BaseModel):
    """Structured logging settings."""

    level: str = "INFO"
    json_output: bool = Field(default=True, alias="json")
    dir: str = "logs"

    model_config = {"populate_by_name": True}


class Secrets(BaseSettings):
    """Credentials and secrets from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tradeify_username: str = Field(default="", alias="TRADEIFY_USERNAME")
    tradeify_password: str = Field(default="", alias="TRADEIFY_PASSWORD")
    tradeify_totp_secret: str = Field(default="", alias="TRADEIFY_TOTP_SECRET")
    alert_email: str = Field(default="", alias="ALERT_EMAIL")
    smtp_url: str = Field(default="", alias="SMTP_URL")


class Settings(BaseModel):
    """Merged application settings."""

    tradeify: TradeifyConfig
    browser: BrowserConfig
    sync: SyncConfig
    storage: StorageConfig
    integration: IntegrationConfig
    instruments: dict[str, InstrumentSpec]
    logging: LoggingConfig
    secrets: Secrets
    project_root: Path = _PROJECT_ROOT
    selectors_path: Path = _PROJECT_ROOT / "selectors.yaml"

    @classmethod
    def load(
        cls,
        config_path: Path | None = None,
        env_path: Path | None = None,
    ) -> Settings:
        """Load and validate settings from YAML and environment."""
        root = _PROJECT_ROOT
        cfg_file = config_path or (root / "config.yaml")
        if not cfg_file.exists():
            raise ConfigError(f"Config file not found: {cfg_file}")

        with cfg_file.open(encoding="utf-8") as fh:
            raw: dict[str, Any] = yaml.safe_load(fh) or {}

        env_file = env_path or (root / ".env")
        if env_file.exists():
            secrets = Secrets(_env_file=str(env_file))  # type: ignore[call-arg]
        else:
            secrets = Secrets()

        try:
            settings = cls(
                tradeify=TradeifyConfig(**raw.get("tradeify", {})),
                browser=BrowserConfig(**raw.get("browser", {})),
                sync=SyncConfig(**raw.get("sync", {})),
                storage=StorageConfig(**raw.get("storage", {})),
                integration=IntegrationConfig(**raw.get("integration", {})),
                instruments={
                    k: InstrumentSpec(**v) for k, v in raw.get("instruments", {}).items()
                },
                logging=LoggingConfig(**raw.get("logging", {})),
                secrets=secrets,
            )
        except Exception as exc:
            raise ConfigError(f"Invalid configuration: {exc}") from exc

        settings._validate()
        settings._ensure_dirs()
        return settings

    def _validate(self) -> None:
        """Run cross-field validation."""
        if self.sync.cadence_minutes < self.sync.min_cadence_minutes:
            raise ConfigError(
                f"cadence_minutes ({self.sync.cadence_minutes}) must be >= "
                f"min_cadence_minutes ({self.sync.min_cadence_minutes})"
            )

    def _ensure_dirs(self) -> None:
        """Create required parent directories."""
        for rel in (
            self.browser.session_path,
            self.storage.sqlite_path,
            self.storage.parquet_dir,
            self.logging.dir,
            "data/downloads",
            "data/sessions/profile",
            "screenshots",
        ):
            path = self.project_root / rel
            if path.suffix:
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)

    def resolve(self, rel_path: str) -> Path:
        """Resolve a config-relative path to an absolute path."""
        return self.project_root / rel_path

    def page_url(self, page_key: str) -> str:
        """Build a dashboard URL for a page key."""
        paths = {
            "login": self.tradeify.login_path,
            "dashboard": "/dashboard",
            "accounts": "/accounts",
            "trades": "/trades",
            "positions": "/positions",
            "payouts": "/payouts",
        }
        path = paths.get(page_key, f"/{page_key}")
        return f"{self.tradeify.base_url}{path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings.load()


def load_selectors(path: Path | None = None) -> dict[str, Any]:
    """Load selectors.yaml as a dict."""
    selectors_file = path or (_PROJECT_ROOT / "selectors.yaml")
    if not selectors_file.exists():
        raise ConfigError(f"Selectors file not found: {selectors_file}")
    with selectors_file.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}
    return data