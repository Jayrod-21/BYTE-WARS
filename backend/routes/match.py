"""
routes/match.py — Match API endpoints for BYTE Wars.

Provides match orchestration:
- POST   /matches           — Create a new match (lobby with 2-4 champion IDs)
- POST   /matches/{id}/start — Start a pending match (async execution)
- GET    /matches/{id}      — Retrieve match status and results
- GET    /matches           — List all matches (optional status filter)

Matches run asynchronously — create, start, then poll GET for results.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from services.match_service import MatchService
from routes.champion import _champions_store
from routes.auth import get_current_user


router = APIRouter(prefix="/matches", tags=["Matches"])
_service = MatchService()


class MatchCreate(BaseModel):
    """Request to create a new match."""
    champion_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2-4 champion IDs to enter the match",
    )


class MatchResponse(BaseModel):
    """Match data returned by the API."""
    id: str
    status: str
    champion_ids: list[str]
    champion_names: list[str]
    winner_id: str | None
    winner_name: str | None
    total_turns: int
    turn_history: list[dict]
    created_at: str | None
    started_at: str | None
    resolved_at: str | None
    loot_chest_id: str | None = None
    loot_chest_items: list[dict] = []


@router.post("", response_model=MatchResponse, status_code=201)
async def create_match(data: MatchCreate, user: dict = Depends(get_current_user)) -> dict:
    """
    Create a new match with 2-4 champions.

    Validates that all champion IDs exist and creates a pending match.
    Call POST /matches/{id}/start to begin execution.
    """
    # Look up champion data for each ID
    champion_data_list = []
    for cid in data.champion_ids:
        champ = _champions_store.get(cid)
        if champ is None:
            raise HTTPException(
                status_code=404,
                detail=f"Champion '{cid}' not found",
            )
        champion_data_list.append(champ)

    try:
        match_data = _service.create_match(champion_data_list)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _service.to_response(match_data)


@router.post("/{match_id}/start", response_model=MatchResponse)
async def start_match(match_id: str, user: dict = Depends(get_current_user)) -> dict:
    """
    Start a pending match. The battle runs asynchronously in the background.

    Poll GET /matches/{id} to check status and get results when complete.
    """
    try:
        match_data = await _service.start_match(match_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _service.to_response(match_data)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str) -> dict:
    """
    Retrieve match status and results.

    Returns full turn history once the match is complete.
    """
    match_data = _service.get_match(match_id)
    if match_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Match '{match_id}' not found",
        )
    return _service.to_response(match_data)


@router.get("", response_model=list[MatchResponse])
async def list_matches(status: str | None = None) -> list[dict]:
    """
    List all matches, optionally filtered by status.

    Status values: pending, active, complete, timed_out
    """
    matches = _service.list_matches(status=status)
    return [_service.to_response(m) for m in matches]
