"""
routes/champion.py — Champion API endpoints for BYTE Wars.

Provides CRUD operations for champions:
- POST   /champions      — Create a new champion
- GET    /champions/{id} — Retrieve a champion's profile
- PATCH  /champions/{id} — Update a champion (no base gear changes)
- GET    /champions      — List all champions (optional filter by archetype)

All endpoints validate input via Pydantic schemas and enforce the
core rules: slot limits, base gear protection, API key encryption.
"""

import uuid
from fastapi import APIRouter, HTTPException

from schemas.champion import ChampionCreate, ChampionUpdate, ChampionResponse
from services.champion_service import ChampionService


# Create the router for champion endpoints
router = APIRouter(prefix="/champions", tags=["Champions"])

# In-memory storage for Phase 3 (replaced with DB queries in Phase 4)
# Using a dict keyed by champion ID string for quick lookups
_champions_store: dict[str, dict] = {}

# Service instance for business logic
_service = ChampionService()


@router.post("", response_model=ChampionResponse, status_code=201)
async def create_champion(data: ChampionCreate) -> dict:
    """
    Create a new champion.

    The champion receives default stats and base gear based on the chosen
    archetype. Base gear is permanent and cannot be removed later.

    Args:
        data: ChampionCreate schema with name, archetype, and optional fields.

    Returns:
        The created champion's full profile (API key redacted).
    """
    try:
        champion_data = _service.build_champion_data(
            name=data.name,
            archetype=data.archetype,
            system_prompt=data.system_prompt,
            gear_slots=data.gear_slots,
            skill_slots=data.skill_slots,
            api_key=data.api_key,
            model=data.model,
            owner_wallet=data.owner_wallet,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store in memory (Phase 4 will use PostgreSQL)
    champion_id = str(champion_data["id"])
    _champions_store[champion_id] = champion_data

    return _service.to_response(champion_data)


@router.get("/{champion_id}", response_model=ChampionResponse)
async def get_champion(champion_id: str) -> dict:
    """
    Retrieve a champion's profile by ID.

    Args:
        champion_id: UUID string of the champion to retrieve.

    Returns:
        The champion's full profile (API key redacted).

    Raises:
        404: If the champion ID doesn't exist.
    """
    champion = _champions_store.get(champion_id)
    if champion is None:
        raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' not found")

    return _service.to_response(champion)


@router.patch("/{champion_id}", response_model=ChampionResponse)
async def update_champion(champion_id: str, data: ChampionUpdate) -> dict:
    """
    Update an existing champion.

    Rules enforced:
    - Cannot modify base gear (permanent, core rule #3)
    - Cannot change archetype after creation
    - Cannot exceed gear slot (6) or skill slot (4) limits
    - API key updates are re-encrypted

    Args:
        champion_id: UUID string of the champion to update.
        data: ChampionUpdate schema with fields to change.

    Returns:
        The updated champion profile (API key redacted).

    Raises:
        404: If the champion ID doesn't exist.
        400: If the update violates any rules.
    """
    champion = _champions_store.get(champion_id)
    if champion is None:
        raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' not found")

    # Build updates dict from non-None fields
    updates = data.model_dump(exclude_unset=True)

    # Validate and apply updates
    updated_data, errors = _service.validate_update(champion, updates)

    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    # Save updated champion
    _champions_store[champion_id] = updated_data

    return _service.to_response(updated_data)


@router.get("", response_model=list[ChampionResponse])
async def list_champions(archetype: str | None = None) -> list[dict]:
    """
    List all champions, optionally filtered by archetype.

    Args:
        archetype: Optional filter — only return champions of this archetype.

    Returns:
        List of champion profiles (API keys redacted).
    """
    champions = _champions_store.values()

    if archetype:
        archetype = archetype.lower().strip()
        champions = [c for c in champions if c.get("archetype") == archetype]

    return [_service.to_response(c) for c in champions]


# --- Utility for testing ---
def clear_store():
    """Clear the in-memory champion store. Used by tests."""
    _champions_store.clear()
