"""
models/match.py — Match data model for BYTE Wars.

Defines the Match table in PostgreSQL. A Match tracks an entire battle between
2-4 champions, including status, turn history, and the winner.

Match statuses:
- pending:   Match created, waiting for all champions to join
- active:    Battle in progress
- complete:  Winner determined
- timed_out: Turn limit exceeded, all remaining bots lose
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Match(Base):
    """
    A Match represents a single battle between 2-4 champions.

    The turn_history field stores a JSON log of every action and resolution
    that occurred during the match, enabling full playback reconstruction
    in Phase 5.
    """

    __tablename__ = "matches"

    # --- Identity ---
    # Unique match ID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # --- Status ---
    # Match lifecycle: pending → active → complete | timed_out
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # --- Participants ---
    # List of champion IDs participating in this match (2-4 champions)
    champion_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # --- Battle History ---
    # Complete turn-by-turn log of every action, roll, damage, and HP change
    # Structure: list of turn objects, each containing actions and resolutions
    turn_history: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # --- Result ---
    # UUID of the winning champion (null until match is resolved)
    winner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # --- Timestamps ---
    # When the match was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # When the match was resolved (null until complete or timed_out)
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
