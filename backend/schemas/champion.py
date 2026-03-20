"""
schemas/champion.py — Pydantic schemas for Champion API endpoints.

Defines the request and response shapes for champion CRUD operations:
- ChampionCreate: POST /champions — create a new champion
- ChampionUpdate: PATCH /champions/{id} — update an existing champion
- ChampionResponse: GET /champions/{id} — what the API returns

Validation rules:
- Archetype must be one of: tank, assassin, mage, ranger, support
- Gear slots max 6, skill slots max 4
- Base gear cannot be modified after creation
- System prompt is optional (can be empty string)
- API key is write-only (never returned in responses)
"""

from pydantic import BaseModel, Field, field_validator
from engine.archetypes import VALID_ARCHETYPES, MAX_GEAR_SLOTS, MAX_SKILL_SLOTS


class ChampionCreate(BaseModel):
    """
    Request schema for creating a new champion (POST /champions).

    Only name and archetype are required. Everything else has sensible defaults
    based on the chosen archetype.
    """
    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name for the champion",
    )
    archetype: str = Field(
        ...,
        description="Champion archetype: tank, assassin, mage, ranger, or support",
    )

    # Optional fields — defaults applied from archetype
    system_prompt: str = Field(
        default="",
        max_length=5000,
        description="Custom strategy/personality prompt for the AI",
    )
    gear_slots: list[dict] = Field(
        default_factory=list,
        description="Equipped gear items (max 6 slots)",
    )
    skill_slots: list[dict] = Field(
        default_factory=list,
        description="Equipped skill items (max 4 slots)",
    )

    # AI provider config — optional at creation
    api_key: str | None = Field(
        default=None,
        description="AI provider API key (will be encrypted at rest)",
    )
    model: str = Field(
        default="claude-sonnet-4-6",
        max_length=50,
        description="AI model identifier",
    )

    # Optional owner info
    owner_wallet: str | None = Field(
        default=None,
        max_length=64,
        description="Solana wallet address of the owner",
    )

    @field_validator("archetype")
    @classmethod
    def validate_archetype(cls, v: str) -> str:
        """Archetype must be one of the 5 valid types."""
        v = v.lower().strip()
        if v not in VALID_ARCHETYPES:
            raise ValueError(
                f"Invalid archetype '{v}'. Must be one of: {', '.join(sorted(VALID_ARCHETYPES))}"
            )
        return v

    @field_validator("gear_slots")
    @classmethod
    def validate_gear_slots(cls, v: list) -> list:
        """Cannot exceed max gear slot limit."""
        if len(v) > MAX_GEAR_SLOTS:
            raise ValueError(
                f"Too many gear items ({len(v)}). Maximum is {MAX_GEAR_SLOTS}."
            )
        return v

    @field_validator("skill_slots")
    @classmethod
    def validate_skill_slots(cls, v: list) -> list:
        """Cannot exceed max skill slot limit."""
        if len(v) > MAX_SKILL_SLOTS:
            raise ValueError(
                f"Too many skills ({len(v)}). Maximum is {MAX_SKILL_SLOTS}."
            )
        return v


class ChampionUpdate(BaseModel):
    """
    Request schema for updating a champion (PATCH /champions/{id}).

    All fields are optional — only provided fields are updated.
    Base gear CANNOT be modified (core rule #3).
    Archetype cannot be changed after creation.
    """
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=5000,
    )
    gear_slots: list[dict] | None = Field(
        default=None,
        description="Replace gear loadout (base gear remains untouched)",
    )
    skill_slots: list[dict] | None = Field(
        default=None,
        description="Replace skill loadout",
    )
    api_key: str | None = Field(
        default=None,
        description="Update AI provider API key",
    )
    model: str | None = Field(
        default=None,
        max_length=50,
    )

    @field_validator("gear_slots")
    @classmethod
    def validate_gear_slots(cls, v: list | None) -> list | None:
        if v is not None and len(v) > MAX_GEAR_SLOTS:
            raise ValueError(
                f"Too many gear items ({len(v)}). Maximum is {MAX_GEAR_SLOTS}."
            )
        return v

    @field_validator("skill_slots")
    @classmethod
    def validate_skill_slots(cls, v: list | None) -> list | None:
        if v is not None and len(v) > MAX_SKILL_SLOTS:
            raise ValueError(
                f"Too many skills ({len(v)}). Maximum is {MAX_SKILL_SLOTS}."
            )
        return v


class ChampionResponse(BaseModel):
    """
    Response schema for champion data returned by the API.

    Note: api_key is NEVER included in responses (write-only).
    has_api_key indicates whether one is set.
    """
    id: str
    name: str
    archetype: str
    system_prompt: str
    stats: dict
    gear_slots: list[dict]
    skill_slots: list[dict]
    base_gear: list[dict]
    model: str | None
    owner_wallet: str | None
    has_api_key: bool  # True if an API key is stored, without revealing it

    class Config:
        from_attributes = True
