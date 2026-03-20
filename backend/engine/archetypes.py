"""
engine/archetypes.py — Archetype definitions for BYTE Wars champions.

Each archetype defines:
- Default stat distribution (health, strength, endurance)
- Base gear (PERMANENT — cannot be removed, core rule #3)
- Description for the champion builder UI

The 5 archetypes represent different playstyles:
- Tank: High health and endurance, low strength. Outlasts opponents.
- Assassin: Low health, high strength. Kills fast or dies fast.
- Mage: Medium health, very high strength, low endurance. Glass cannon.
- Ranger: Balanced stats. Jack of all trades.
- Support: High endurance, moderate health. Focuses on survival and healing.
"""

ARCHETYPES = {
    "tank": {
        "name": "tank",
        "description": "High durability, outlasts opponents with superior defense.",
        "default_stats": {
            "health": 150,
            "strength": 35,
            "endurance": 75,
        },
        "base_gear": [
            {
                "name": "iron_shield",
                "type": "gear",
                "description": "A sturdy iron shield. Grants passive defense.",
                "stat_bonus": {"endurance": 5},
            },
            {
                "name": "heavy_armor",
                "type": "gear",
                "description": "Thick plate armor. Increases max health.",
                "stat_bonus": {"health": 10},
            },
        ],
    },
    "assassin": {
        "name": "assassin",
        "description": "Fast and deadly. Strikes hard but can't take many hits.",
        "default_stats": {
            "health": 80,
            "strength": 80,
            "endurance": 40,
        },
        "base_gear": [
            {
                "name": "shadow_dagger",
                "type": "gear",
                "description": "A razor-sharp dagger. Boosts attack power.",
                "stat_bonus": {"strength": 8},
            },
            {
                "name": "light_cloak",
                "type": "gear",
                "description": "A dark cloak for quick movement.",
                "stat_bonus": {"endurance": 3},
            },
        ],
    },
    "mage": {
        "name": "mage",
        "description": "Raw power at the cost of survivability. Glass cannon.",
        "default_stats": {
            "health": 90,
            "strength": 90,
            "endurance": 25,
        },
        "base_gear": [
            {
                "name": "arcane_staff",
                "type": "gear",
                "description": "A staff crackling with energy. Massive strength boost.",
                "stat_bonus": {"strength": 10},
            },
            {
                "name": "mana_robes",
                "type": "gear",
                "description": "Enchanted robes. Light protection.",
                "stat_bonus": {"health": 5},
            },
        ],
    },
    "ranger": {
        "name": "ranger",
        "description": "Balanced fighter. Adaptable to any situation.",
        "default_stats": {
            "health": 110,
            "strength": 55,
            "endurance": 55,
        },
        "base_gear": [
            {
                "name": "composite_bow",
                "type": "gear",
                "description": "A reliable ranged weapon. Moderate damage.",
                "stat_bonus": {"strength": 5},
            },
            {
                "name": "leather_armor",
                "type": "gear",
                "description": "Flexible leather armor. Balanced protection.",
                "stat_bonus": {"endurance": 5},
            },
        ],
    },
    "support": {
        "name": "support",
        "description": "Survival specialist. Heals and outlasts through endurance.",
        "default_stats": {
            "health": 120,
            "strength": 30,
            "endurance": 70,
        },
        "base_gear": [
            {
                "name": "healing_totem",
                "type": "gear",
                "description": "A restorative totem. Boosts healing effectiveness.",
                "stat_bonus": {"endurance": 8},
            },
            {
                "name": "ward_amulet",
                "type": "gear",
                "description": "Protective amulet. Increases health pool.",
                "stat_bonus": {"health": 8},
            },
        ],
    },
}

# Valid archetype names for validation
VALID_ARCHETYPES = set(ARCHETYPES.keys())

# Slot limits (core rule — enforces strategic tradeoffs)
MAX_GEAR_SLOTS = 6
MAX_SKILL_SLOTS = 4


def get_archetype(name: str) -> dict | None:
    """Look up an archetype by name. Returns None if not found."""
    return ARCHETYPES.get(name)


def get_default_stats(archetype: str) -> dict:
    """Get the default stat distribution for an archetype."""
    arch = ARCHETYPES.get(archetype)
    if arch is None:
        return {"health": 100, "strength": 50, "endurance": 50}
    return dict(arch["default_stats"])


def get_base_gear(archetype: str) -> list[dict]:
    """Get the permanent base gear for an archetype."""
    arch = ARCHETYPES.get(archetype)
    if arch is None:
        return []
    return list(arch["base_gear"])
