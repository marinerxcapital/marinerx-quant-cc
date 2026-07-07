"""Strategy Registry API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mcc.storage.repositories import StrategyRepository

router = APIRouter(prefix="/api/strategies", tags=["strategies"])
_repo = StrategyRepository()


class StrategyCreate(BaseModel):
    name: str
    instrument: str
    timeframe: str
    hypothesis: str
    entry_rules: str
    exit_rules: str
    risk_rules: str
    description: str = ""
    strategy_id: str | None = None
    owner_agent: str = "ResearchLab"
    parameters_json: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    instrument: str | None = None
    timeframe: str | None = None
    status: str | None = None
    hypothesis: str | None = None
    entry_rules: str | None = None
    exit_rules: str | None = None
    risk_rules: str | None = None
    parameters_json: dict[str, Any] | None = None
    tags: list[str] | None = None
    latest_verdict: str | None = None
    change_note: str | None = None


@router.get("")
def list_strategies(
    status: str | None = None,
    instrument: str | None = None,
    timeframe: str | None = None,
    tag: str | None = None,
    include_archived: bool = False,
) -> dict[str, Any]:
    items = _repo.list_strategies(
        status=status, instrument=instrument, timeframe=timeframe,
        tag=tag, include_archived=include_archived,
    )
    return {"strategies": items, "count": len(items)}


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str) -> dict[str, Any]:
    item = _repo.get(strategy_id)
    if not item:
        raise HTTPException(404, "Strategy not found")
    return item


@router.post("")
def create_strategy(body: StrategyCreate) -> dict[str, Any]:
    return _repo.create(body.model_dump())


@router.patch("/{strategy_id}")
def update_strategy(strategy_id: str, body: StrategyUpdate) -> dict[str, Any]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        item = _repo.update(strategy_id, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not item:
        raise HTTPException(404, "Strategy not found")
    return item


@router.post("/{strategy_id}/archive")
def archive_strategy(strategy_id: str) -> dict[str, Any]:
    item = _repo.archive(strategy_id)
    if not item:
        raise HTTPException(404, "Strategy not found")
    return item