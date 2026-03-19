"""
models/champion.py — Champion data model for BYTE Wars.

Defines the Champion table in PostgreSQL. A Champion represents an AI fighter
with stats, gear, skills, and a custom system prompt that controls its behavior.

Fields match the champion structure from BYTE_WARS_CONTEXT.md:
- Unique ID, owner info, name, and archetype
- Stats dict (health, strength, endurance)
- Gear slots (max 6), skill slots (max 4), and permanent base gear
- Encrypted API key and model selection for the AI provider
"""

import uuid

from sqlalchemy import String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Champion(Base):
    """
    A Champion is an AI-controlled fighter in BYTE Wars.

    Each champion has:
    - A custom system prompt that defines its battle strategy/personality
    - An archetype (tank, assassin, mage, ranger, support)
    - Stats that modify damage, defense, and initiative
    - Gear and skill slots (NFT items in later phases)
    - Base gear that can never be removed (floor protection)
    """

    __tablename__ = "champions"

    # --- Identity ---
    # Unique champion ID, auto-generated UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The Solana wallet address of the champion's owner
    owner_wallet: Mapped[str] = mapped_column(String(64), nullable=True)

    # Internal user ID of the owner
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Display name for the champion
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # --- AI Configuration ---
    # The system prompt that controls this champion's battle behavior
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # Primary archetype determines base loadout and stat distribution
    archetype: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ranger"
    )

    # --- Stats ---
    # Stats dictionary: health, strength, endurance (and future expansions)
    # Stored as JSON for flexibility
    stats: Mapped[dict] = mapped_column(
        JSON, nullable=False,
        default=lambda: {"health": 100, "strength": 50, "endurance": 50}
    )

    # --- Gear & Skills ---
    # Gear slots — max 6 items (NFT items in Phase 7+)
    gear_slots: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Skill slots — max 4 skills (NFT skills in Phase 7+)
    skill_slots: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Base gear — PERMANENT, cannot be removed or lost (core rule #3)
    base_gear: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # --- AI Provider ---
    # Encrypted API key for the AI model provider (encryption in Phase 3)
    api_key: Mapped[str] = mapped_column(String(512), nullable=True)

    # Which AI model to use (e.g., "claude-sonnet-4-6", "gpt-4o", "gemini-pro")
    model: Mapped[str] = mapped_column(
        String(50), nullable=True, default="claude-sonnet-4-6"
    )
