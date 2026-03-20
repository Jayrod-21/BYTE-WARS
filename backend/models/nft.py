"""
models/nft.py — NFT data model for BYTE Wars.

Defines the structure for NFT items (gear and skills) that champions
can equip. NFTs have:
- Unique ID and on-chain mint address
- Type: gear (passive stat bonuses) or skill (MCP tool action)
- Rarity tier: common, uncommon, rare, legendary
- Stat bonuses (for gear) or action definition (for skills)
- Archetype affinity (any archetype can equip, but affinity gives bonus)
- Owner wallet address

Phase 7: Uses stub/mock NFTs for testing. Phase 9 will mint real NFTs on Solana.
"""

import uuid
import random
from dataclasses import dataclass, field, asdict
from enum import Enum


class NFTType(str, Enum):
    GEAR = "gear"
    SKILL = "skill"


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


# Rarity multipliers for stat bonuses
RARITY_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.5,
    "rare": 2.0,
    "legendary": 3.0,
}

# Rarity colors for UI
RARITY_COLORS = {
    "common": "#aaaaaa",
    "uncommon": "#44ff44",
    "rare": "#4488ff",
    "legendary": "#ffaa00",
}


@dataclass
class NFTItem:
    """
    An NFT item that can be equipped by a champion.

    Gear items provide passive stat bonuses.
    Skill items register as MCP tools during battle.
    """
    id: str
    name: str
    description: str
    nft_type: str  # "gear" or "skill"
    rarity: str    # "common", "uncommon", "rare", "legendary"
    archetype_affinity: str  # Which archetype gets a bonus (or "any")
    owner_wallet: str | None = None
    mint_address: str | None = None  # Solana mint address (Phase 9)

    # Gear-specific fields
    stat_bonuses: dict = field(default_factory=dict)  # {"health": 10, "strength": 5}

    # Skill-specific fields (defines an MCP tool action)
    skill_action: dict | None = None  # Full action definition for ToolRegistry

    def to_dict(self) -> dict:
        return asdict(self)

    def get_effective_bonuses(self, champion_archetype: str) -> dict:
        """
        Get stat bonuses adjusted for archetype affinity.

        If the champion's archetype matches the item's affinity,
        bonuses are increased by 25%.

        Args:
            champion_archetype: The champion's archetype.

        Returns:
            Dict of stat bonuses (possibly boosted).
        """
        if not self.stat_bonuses:
            return {}

        multiplier = 1.0
        if self.archetype_affinity != "any" and self.archetype_affinity == champion_archetype:
            multiplier = 1.25  # 25% affinity bonus

        return {
            stat: round(value * multiplier)
            for stat, value in self.stat_bonuses.items()
        }


# =============================================
# NFT CATALOG — Stub items for testing (Phase 7)
# Phase 9 will generate these from on-chain data
# =============================================

GEAR_CATALOG = [
    # --- Common Gear ---
    {
        "name": "rusty_blade",
        "description": "A worn blade. Adds minor attack power.",
        "rarity": "common",
        "archetype_affinity": "assassin",
        "stat_bonuses": {"strength": 3},
    },
    {
        "name": "wooden_buckler",
        "description": "A simple wooden shield. Slight defense boost.",
        "rarity": "common",
        "archetype_affinity": "tank",
        "stat_bonuses": {"endurance": 3},
    },
    {
        "name": "cloth_bandage",
        "description": "Basic bandages. Small health increase.",
        "rarity": "common",
        "archetype_affinity": "support",
        "stat_bonuses": {"health": 5},
    },
    {
        "name": "hunting_knife",
        "description": "A sharp knife for quick cuts.",
        "rarity": "common",
        "archetype_affinity": "ranger",
        "stat_bonuses": {"strength": 2, "endurance": 1},
    },
    {
        "name": "spell_scroll",
        "description": "A minor enchantment scroll.",
        "rarity": "common",
        "archetype_affinity": "mage",
        "stat_bonuses": {"strength": 4},
    },

    # --- Uncommon Gear ---
    {
        "name": "steel_gauntlets",
        "description": "Reinforced gauntlets. Good attack boost.",
        "rarity": "uncommon",
        "archetype_affinity": "tank",
        "stat_bonuses": {"strength": 5, "endurance": 3},
    },
    {
        "name": "shadow_cowl",
        "description": "A hood that sharpens reflexes.",
        "rarity": "uncommon",
        "archetype_affinity": "assassin",
        "stat_bonuses": {"strength": 6, "endurance": 2},
    },
    {
        "name": "crystal_focus",
        "description": "A crystal that amplifies magical power.",
        "rarity": "uncommon",
        "archetype_affinity": "mage",
        "stat_bonuses": {"strength": 7},
    },
    {
        "name": "ranger_cloak",
        "description": "A cloak of the wilds. Balanced protection.",
        "rarity": "uncommon",
        "archetype_affinity": "ranger",
        "stat_bonuses": {"health": 8, "endurance": 4},
    },
    {
        "name": "medics_kit",
        "description": "A field medic's toolkit. Boosts healing.",
        "rarity": "uncommon",
        "archetype_affinity": "support",
        "stat_bonuses": {"endurance": 6, "health": 5},
    },

    # --- Rare Gear ---
    {
        "name": "adamantine_plate",
        "description": "Nearly indestructible armor. Massive defense.",
        "rarity": "rare",
        "archetype_affinity": "tank",
        "stat_bonuses": {"health": 15, "endurance": 10},
    },
    {
        "name": "void_daggers",
        "description": "Daggers from the void. Devastating strikes.",
        "rarity": "rare",
        "archetype_affinity": "assassin",
        "stat_bonuses": {"strength": 12},
    },
    {
        "name": "archmage_tome",
        "description": "Ancient tome of supreme power.",
        "rarity": "rare",
        "archetype_affinity": "mage",
        "stat_bonuses": {"strength": 14, "health": 5},
    },
    {
        "name": "phoenix_amulet",
        "description": "A legendary healer's relic.",
        "rarity": "rare",
        "archetype_affinity": "support",
        "stat_bonuses": {"endurance": 12, "health": 10},
    },

    # --- Legendary Gear ---
    {
        "name": "worldbreaker_hammer",
        "description": "A hammer that shatters reality itself.",
        "rarity": "legendary",
        "archetype_affinity": "tank",
        "stat_bonuses": {"strength": 15, "health": 20, "endurance": 10},
    },
    {
        "name": "deaths_whisper",
        "description": "The blade that killed a god.",
        "rarity": "legendary",
        "archetype_affinity": "assassin",
        "stat_bonuses": {"strength": 25},
    },
    {
        "name": "infinity_orb",
        "description": "Contains the power of a collapsing star.",
        "rarity": "legendary",
        "archetype_affinity": "mage",
        "stat_bonuses": {"strength": 22, "health": 10},
    },
]

SKILL_CATALOG = [
    # --- Common Skills ---
    {
        "name": "quick_slash",
        "description": "A swift slashing attack. Low cost, low damage.",
        "rarity": "common",
        "archetype_affinity": "assassin",
        "skill_action": {
            "name": "quick_slash",
            "description": "A swift slashing attack.",
            "action_point_cost": 1,
            "damage_range": [4, 10],
            "heal_range": None,
            "stat_requirement": "strength",
            "target": "single_enemy",
            "is_defense": False,
        },
    },
    {
        "name": "minor_ward",
        "description": "A small protective ward. Reduces damage slightly.",
        "rarity": "common",
        "archetype_affinity": "support",
        "skill_action": {
            "name": "minor_ward",
            "description": "A protective ward. Reduces incoming damage by 20%.",
            "action_point_cost": 1,
            "damage_range": None,
            "heal_range": None,
            "stat_requirement": "endurance",
            "target": "self",
            "is_defense": True,
        },
    },

    # --- Uncommon Skills ---
    {
        "name": "poison_strike",
        "description": "A venomous attack that deals extra damage.",
        "rarity": "uncommon",
        "archetype_affinity": "assassin",
        "skill_action": {
            "name": "poison_strike",
            "description": "A poisoned blade strike. Extra damage.",
            "action_point_cost": 2,
            "damage_range": [12, 22],
            "heal_range": None,
            "stat_requirement": "strength",
            "target": "single_enemy",
            "is_defense": False,
        },
    },
    {
        "name": "greater_heal",
        "description": "A powerful healing spell.",
        "rarity": "uncommon",
        "archetype_affinity": "support",
        "skill_action": {
            "name": "greater_heal",
            "description": "A powerful healing spell. Restores significant HP.",
            "action_point_cost": 2,
            "damage_range": None,
            "heal_range": [18, 30],
            "stat_requirement": "endurance",
            "target": "self",
            "is_defense": False,
        },
    },
    {
        "name": "fireball",
        "description": "A blazing fireball attack.",
        "rarity": "uncommon",
        "archetype_affinity": "mage",
        "skill_action": {
            "name": "fireball",
            "description": "Hurl a fireball at your enemy.",
            "action_point_cost": 2,
            "damage_range": [14, 24],
            "heal_range": None,
            "stat_requirement": "strength",
            "target": "single_enemy",
            "is_defense": False,
        },
    },

    # --- Rare Skills ---
    {
        "name": "executioners_blow",
        "description": "A devastating finisher against wounded targets.",
        "rarity": "rare",
        "archetype_affinity": "assassin",
        "skill_action": {
            "name": "executioners_blow",
            "description": "A devastating finisher. Massive damage.",
            "action_point_cost": 3,
            "damage_range": [28, 45],
            "heal_range": None,
            "stat_requirement": "strength",
            "target": "single_enemy",
            "is_defense": False,
        },
    },
    {
        "name": "divine_intervention",
        "description": "Calls upon divine power for massive healing.",
        "rarity": "rare",
        "archetype_affinity": "support",
        "skill_action": {
            "name": "divine_intervention",
            "description": "Divine healing. Massive HP restoration.",
            "action_point_cost": 3,
            "damage_range": None,
            "heal_range": [30, 50],
            "stat_requirement": "endurance",
            "target": "self",
            "is_defense": False,
        },
    },

    # --- Legendary Skill ---
    {
        "name": "meteor_storm",
        "description": "Calls down a storm of meteors.",
        "rarity": "legendary",
        "archetype_affinity": "mage",
        "skill_action": {
            "name": "meteor_storm",
            "description": "Rain meteors upon your enemy. Devastating damage.",
            "action_point_cost": 3,
            "damage_range": [35, 55],
            "heal_range": None,
            "stat_requirement": "strength",
            "target": "single_enemy",
            "is_defense": False,
        },
    },
]


def generate_stub_nft(
    catalog_entry: dict,
    nft_type: str,
    owner_wallet: str | None = None,
) -> NFTItem:
    """
    Generate a stub NFT from a catalog entry.

    Args:
        catalog_entry: Entry from GEAR_CATALOG or SKILL_CATALOG.
        nft_type: "gear" or "skill".
        owner_wallet: Optional owner wallet address.

    Returns:
        NFTItem instance.
    """
    return NFTItem(
        id=str(uuid.uuid4()),
        name=catalog_entry["name"],
        description=catalog_entry["description"],
        nft_type=nft_type,
        rarity=catalog_entry["rarity"],
        archetype_affinity=catalog_entry["archetype_affinity"],
        owner_wallet=owner_wallet,
        mint_address=f"stub_{uuid.uuid4().hex[:16]}",
        stat_bonuses=catalog_entry.get("stat_bonuses", {}),
        skill_action=catalog_entry.get("skill_action"),
    )


def generate_starter_inventory(owner_wallet: str | None = None) -> list[NFTItem]:
    """
    Generate a starter inventory of stub NFTs for testing.

    Gives the user a mix of gear and skills across rarities.

    Returns:
        List of 6 NFTItems (4 gear + 2 skills).
    """
    gear_picks = random.sample(GEAR_CATALOG, min(4, len(GEAR_CATALOG)))
    skill_picks = random.sample(SKILL_CATALOG, min(2, len(SKILL_CATALOG)))

    items = []
    for g in gear_picks:
        items.append(generate_stub_nft(g, "gear", owner_wallet))
    for s in skill_picks:
        items.append(generate_stub_nft(s, "skill", owner_wallet))

    return items
