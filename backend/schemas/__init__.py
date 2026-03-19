"""
schemas/ — Pydantic request/response schemas for BYTE Wars API.

These schemas validate incoming API data and shape outgoing responses.
"""

from schemas.champion import (
    ChampionCreate,
    ChampionUpdate,
    ChampionResponse,
)

__all__ = ["ChampionCreate", "ChampionUpdate", "ChampionResponse"]
