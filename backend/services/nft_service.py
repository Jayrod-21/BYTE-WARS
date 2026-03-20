"""
services/nft_service.py — NFT inventory and equipment service for BYTE Wars.

Manages NFT items:
- Inventory storage per wallet/user
- Equipping gear and skills to champion slots
- Applying NFT stat bonuses to champion stats for battle
- Registering NFT skill actions as MCP tools
- Generating starter inventories for new users

Phase 7: In-memory storage with stub NFTs.
Phase 9: On-chain NFT verification via Metaplex.
"""

from models.nft import (
    NFTItem,
    NFTType,
    GEAR_CATALOG,
    SKILL_CATALOG,
    generate_stub_nft,
    generate_starter_inventory,
    RARITY_MULTIPLIERS,
)
from engine.archetypes import MAX_GEAR_SLOTS, MAX_SKILL_SLOTS


# In-memory NFT inventory: wallet_or_user_id -> list[NFTItem]
_inventory_store: dict[str, list[NFTItem]] = {}

# NFT lookup by ID for fast access
_nft_lookup: dict[str, NFTItem] = {}


class NFTService:
    """
    Manages NFT inventory, equipment, and battle integration.
    """

    def get_inventory(self, owner_id: str) -> list[dict]:
        """Get all NFT items owned by a user/wallet."""
        items = _inventory_store.get(owner_id, [])
        return [item.to_dict() for item in items]

    def get_nft(self, nft_id: str) -> NFTItem | None:
        """Look up an NFT by its ID."""
        return _nft_lookup.get(nft_id)

    def generate_inventory(self, owner_id: str) -> list[dict]:
        """
        Generate a starter inventory for a new user.

        Only generates if the user doesn't already have items.

        Returns:
            List of generated NFT item dicts.
        """
        if owner_id in _inventory_store and _inventory_store[owner_id]:
            return [item.to_dict() for item in _inventory_store[owner_id]]

        items = generate_starter_inventory(owner_id)
        _inventory_store[owner_id] = items
        for item in items:
            _nft_lookup[item.id] = item
        return [item.to_dict() for item in items]

    def mint_stub_nft(
        self,
        owner_id: str,
        catalog_name: str,
        nft_type: str = "gear",
    ) -> dict | None:
        """
        Mint a specific stub NFT from the catalog.

        Args:
            owner_id: Owner's ID or wallet address.
            catalog_name: Name of the item in the catalog.
            nft_type: "gear" or "skill".

        Returns:
            The minted NFT dict, or None if not found in catalog.
        """
        catalog = GEAR_CATALOG if nft_type == "gear" else SKILL_CATALOG
        entry = next((e for e in catalog if e["name"] == catalog_name), None)
        if entry is None:
            return None

        nft = generate_stub_nft(entry, nft_type, owner_id)
        if owner_id not in _inventory_store:
            _inventory_store[owner_id] = []
        _inventory_store[owner_id].append(nft)
        _nft_lookup[nft.id] = nft
        return nft.to_dict()

    def equip_gear_to_champion(
        self,
        champion_data: dict,
        nft_ids: list[str],
        owner_id: str,
    ) -> tuple[dict, list[str]]:
        """
        Equip NFT gear items to a champion's gear slots.

        Validates:
        - All NFT IDs exist and belong to the owner
        - All items are gear type
        - Does not exceed MAX_GEAR_SLOTS
        - Base gear is untouched (separate from gear_slots)

        Args:
            champion_data: The champion dict to modify.
            nft_ids: List of NFT IDs to equip.
            owner_id: Owner's ID for ownership verification.

        Returns:
            Tuple of (updated_champion, errors).
        """
        errors = []
        gear_items = []

        if len(nft_ids) > MAX_GEAR_SLOTS:
            errors.append(f"Too many gear items ({len(nft_ids)}). Max is {MAX_GEAR_SLOTS}.")
            return champion_data, errors

        for nft_id in nft_ids:
            nft = _nft_lookup.get(nft_id)
            if nft is None:
                errors.append(f"NFT '{nft_id}' not found.")
                continue
            if nft.owner_wallet != owner_id:
                errors.append(f"NFT '{nft.name}' does not belong to you.")
                continue
            if nft.nft_type != "gear":
                errors.append(f"NFT '{nft.name}' is a skill, not gear.")
                continue
            gear_items.append({
                "nft_id": nft.id,
                "name": nft.name,
                "type": "gear",
                "rarity": nft.rarity,
                "stat_bonus": nft.stat_bonuses,
                "description": nft.description,
            })

        if errors:
            return champion_data, errors

        champion_data["gear_slots"] = gear_items
        return champion_data, []

    def equip_skills_to_champion(
        self,
        champion_data: dict,
        nft_ids: list[str],
        owner_id: str,
    ) -> tuple[dict, list[str]]:
        """
        Equip NFT skill items to a champion's skill slots.

        Args:
            champion_data: The champion dict to modify.
            nft_ids: List of NFT skill IDs to equip.
            owner_id: Owner's ID for verification.

        Returns:
            Tuple of (updated_champion, errors).
        """
        errors = []
        skill_items = []

        if len(nft_ids) > MAX_SKILL_SLOTS:
            errors.append(f"Too many skills ({len(nft_ids)}). Max is {MAX_SKILL_SLOTS}.")
            return champion_data, errors

        for nft_id in nft_ids:
            nft = _nft_lookup.get(nft_id)
            if nft is None:
                errors.append(f"NFT '{nft_id}' not found.")
                continue
            if nft.owner_wallet != owner_id:
                errors.append(f"NFT '{nft.name}' does not belong to you.")
                continue
            if nft.nft_type != "skill":
                errors.append(f"NFT '{nft.name}' is gear, not a skill.")
                continue
            if nft.skill_action is None:
                errors.append(f"NFT '{nft.name}' has no skill action defined.")
                continue
            skill_items.append({
                "nft_id": nft.id,
                "name": nft.name,
                "type": "skill",
                "rarity": nft.rarity,
                "skill_action": nft.skill_action,
                "description": nft.description,
            })

        if errors:
            return champion_data, errors

        champion_data["skill_slots"] = skill_items
        return champion_data, []

    def apply_gear_bonuses(
        self,
        champion_data: dict,
    ) -> dict:
        """
        Calculate effective stats for a champion with NFT gear equipped.

        Applies:
        1. Base archetype stats
        2. Base gear bonuses (permanent)
        3. NFT gear slot bonuses (with archetype affinity)

        Args:
            champion_data: Champion dict with stats, base_gear, gear_slots.

        Returns:
            New stats dict with all bonuses applied.
        """
        stats = dict(champion_data.get("stats", {}))
        archetype = champion_data.get("archetype", "ranger")

        # Apply base gear bonuses
        for gear in champion_data.get("base_gear", []):
            for stat, bonus in gear.get("stat_bonus", {}).items():
                stats[stat] = stats.get(stat, 0) + bonus

        # Apply NFT gear slot bonuses
        for gear in champion_data.get("gear_slots", []):
            nft_id = gear.get("nft_id")
            if nft_id:
                nft = _nft_lookup.get(nft_id)
                if nft:
                    effective = nft.get_effective_bonuses(archetype)
                    for stat, bonus in effective.items():
                        stats[stat] = stats.get(stat, 0) + bonus
            else:
                # Legacy gear without NFT reference
                for stat, bonus in gear.get("stat_bonus", {}).items():
                    stats[stat] = stats.get(stat, 0) + bonus

        return stats

    def get_skill_actions(self, champion_data: dict) -> list[dict]:
        """
        Get MCP tool action definitions from equipped NFT skills.

        These get dynamically registered with the ToolRegistry
        before battle starts.

        Args:
            champion_data: Champion dict with skill_slots.

        Returns:
            List of action definition dicts for ToolRegistry.register_tool().
        """
        actions = []
        for skill in champion_data.get("skill_slots", []):
            action = skill.get("skill_action")
            if action:
                actions.append(action)
        return actions


def clear_store():
    """Clear NFT stores. Used by tests."""
    _inventory_store.clear()
    _nft_lookup.clear()
