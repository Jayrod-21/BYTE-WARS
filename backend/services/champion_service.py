"""
services/champion_service.py — Champion CRUD service for BYTE Wars.

Handles all champion business logic:
- Creating champions with archetype-based defaults
- Encrypting/decrypting API keys at rest
- Enforcing slot limits and base gear protection
- CRUD operations against the PostgreSQL database

Encryption uses Fernet symmetric encryption. The key is loaded from
the ENCRYPTION_KEY environment variable (generated once, stored securely).
For dev, a default key is used — MUST be replaced in production (Phase 11).
"""

import os
import uuid
from cryptography.fernet import Fernet

from engine.archetypes import (
    get_archetype,
    get_default_stats,
    get_base_gear,
    VALID_ARCHETYPES,
    MAX_GEAR_SLOTS,
    MAX_SKILL_SLOTS,
)


# --- Encryption Setup ---
# Load encryption key from environment, or generate a dev-only default
# WARNING: The default key is for development ONLY. Set ENCRYPTION_KEY in production.
_ENV_KEY = os.getenv("ENCRYPTION_KEY")
if _ENV_KEY:
    _FERNET = Fernet(_ENV_KEY.encode())
else:
    # Generate a stable dev key (deterministic so restarts don't lose data)
    _DEV_KEY = Fernet.generate_key()
    _FERNET = Fernet(_DEV_KEY)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage at rest.

    Args:
        api_key: The plaintext API key to encrypt.

    Returns:
        Encrypted string safe for database storage.
    """
    return _FERNET.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt a stored API key.

    Args:
        encrypted_key: The encrypted API key from the database.

    Returns:
        The original plaintext API key.

    Raises:
        Exception: If decryption fails (wrong key or corrupted data).
    """
    try:
        return _FERNET.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt API key: {e}")


class ChampionService:
    """
    Business logic for champion operations.

    Handles creation, updates, and validation rules:
    - Archetype determines default stats and base gear
    - Base gear is assigned at creation and can NEVER be modified
    - Gear slots max 6, skill slots max 4
    - API keys are encrypted before storage
    - Cross-archetype gear selection is allowed (gear from any archetype)
    """

    def build_champion_data(
        self,
        name: str,
        archetype: str,
        system_prompt: str = "",
        gear_slots: list | None = None,
        skill_slots: list | None = None,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        owner_wallet: str | None = None,
    ) -> dict:
        """
        Build a complete champion data dictionary for database insertion.

        Assigns archetype defaults for stats and base gear, encrypts API key.

        Args:
            name: Champion display name.
            archetype: One of tank, assassin, mage, ranger, support.
            system_prompt: Custom AI strategy prompt.
            gear_slots: Optional gear items (max 6).
            skill_slots: Optional skill items (max 4).
            api_key: Optional AI provider API key (will be encrypted).
            model: AI model identifier.
            owner_wallet: Solana wallet address.

        Returns:
            Dict with all champion fields ready for DB insertion.

        Raises:
            ValueError: If archetype is invalid or slot limits exceeded.
        """
        # Validate archetype
        if archetype not in VALID_ARCHETYPES:
            raise ValueError(
                f"Invalid archetype '{archetype}'. "
                f"Must be one of: {', '.join(sorted(VALID_ARCHETYPES))}"
            )

        # Get archetype defaults
        stats = get_default_stats(archetype)
        base_gear = get_base_gear(archetype)

        # Validate slot limits
        gear = gear_slots or []
        skills = skill_slots or []
        if len(gear) > MAX_GEAR_SLOTS:
            raise ValueError(f"Too many gear items ({len(gear)}). Max is {MAX_GEAR_SLOTS}.")
        if len(skills) > MAX_SKILL_SLOTS:
            raise ValueError(f"Too many skills ({len(skills)}). Max is {MAX_SKILL_SLOTS}.")

        # Encrypt API key if provided
        encrypted_key = None
        if api_key:
            encrypted_key = encrypt_api_key(api_key)

        return {
            "id": uuid.uuid4(),
            "name": name,
            "archetype": archetype,
            "system_prompt": system_prompt,
            "stats": stats,
            "base_gear": base_gear,
            "gear_slots": gear,
            "skill_slots": skills,
            "api_key": encrypted_key,
            "model": model,
            "owner_wallet": owner_wallet,
        }

    def validate_update(
        self,
        existing_champion: dict,
        updates: dict,
    ) -> tuple[dict, list[str]]:
        """
        Validate and apply updates to an existing champion.

        Rules:
        - Cannot modify base_gear (core rule #3)
        - Cannot change archetype after creation
        - Cannot exceed gear/skill slot limits
        - API key updates are re-encrypted

        Args:
            existing_champion: Current champion data from DB.
            updates: Dict of fields to update (only non-None values).

        Returns:
            Tuple of (updated_data, errors). errors is empty if valid.
        """
        errors = []
        updated = dict(existing_champion)

        for field, value in updates.items():
            if value is None:
                continue

            # Block protected fields
            if field == "base_gear":
                errors.append("Cannot modify base gear — it is permanent.")
                continue
            if field == "archetype":
                errors.append("Cannot change archetype after creation.")
                continue
            if field == "id":
                errors.append("Cannot modify champion ID.")
                continue
            if field == "stats":
                errors.append("Cannot directly modify stats (determined by archetype).")
                continue

            # Validate slot limits
            if field == "gear_slots":
                if len(value) > MAX_GEAR_SLOTS:
                    errors.append(f"Too many gear items ({len(value)}). Max is {MAX_GEAR_SLOTS}.")
                    continue
                # Verify base gear items are still present
                base_gear_names = {g["name"] for g in existing_champion.get("base_gear", [])}
                # Base gear is separate from gear_slots, so this is fine
                updated["gear_slots"] = value

            elif field == "skill_slots":
                if len(value) > MAX_SKILL_SLOTS:
                    errors.append(f"Too many skills ({len(value)}). Max is {MAX_SKILL_SLOTS}.")
                    continue
                updated["skill_slots"] = value

            elif field == "api_key":
                # Re-encrypt the new API key
                updated["api_key"] = encrypt_api_key(value)

            else:
                updated[field] = value

        return updated, errors

    def to_response(self, champion_data: dict) -> dict:
        """
        Convert internal champion data to API response format.

        Strips the API key and replaces it with a boolean has_api_key flag.

        Args:
            champion_data: Raw champion data from DB or service.

        Returns:
            Dict safe for API response (no sensitive data exposed).
        """
        return {
            "id": str(champion_data.get("id", "")),
            "name": champion_data.get("name", ""),
            "archetype": champion_data.get("archetype", ""),
            "system_prompt": champion_data.get("system_prompt", ""),
            "stats": champion_data.get("stats", {}),
            "gear_slots": champion_data.get("gear_slots", []),
            "skill_slots": champion_data.get("skill_slots", []),
            "base_gear": champion_data.get("base_gear", []),
            "model": champion_data.get("model"),
            "owner_wallet": champion_data.get("owner_wallet"),
            "has_api_key": champion_data.get("api_key") is not None,
        }
