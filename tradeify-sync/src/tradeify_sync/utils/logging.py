"""Structured logging with redaction."""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

REDACT_KEYS = frozenset({"password", "token", "secret", "cookie", "html"})

_run_id_var: ContextVar[str] = ContextVar("run_id", default="")


def new_run_id() -> str:
    """Generate and bind a new run_id."""
    rid = uuid.uuid4().hex[:12]
    _run_id_var.set(rid)
    return rid


def get_run_id() -> str:
    """Return the current run_id."""
    return _run_id_var.get()


def _redact_processor(
    _logger: Any,
    _method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Drop sensitive keys from log events."""
    return {k: v for k, v in event_dict.items() if k.lower() not in REDACT_KEYS}


def configure_logging(
    level: str = "INFO",
    json_output: bool = True,
    log_dir: str = "logs",
    *,
    json: bool | None = None,
) -> None:
    """Configure structlog; accepts ``json`` alias for backward compatibility."""
    if json is not None:
        json_output = json
    """Configure structlog with rotating file and console handlers."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / "tradeify_sync.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler(sys.stderr)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[file_handler, console_handler],
        format="%(message)s",
    )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _redact_processor,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name).bind(run_id=get_run_id())