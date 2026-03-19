"""
engine/actions.py — Base MCP tool set for BYTE Wars.

Defines the 5 base combat actions available to all champions. These will become
real MCP tools in Phase 2, but for now they're Python dictionaries that the
battle engine reads to resolve combat.

Each action has:
- name: Unique identifier
- action_point_cost: How many of the 3 per-turn action points this uses
- damage_range: [min, max] for attacks, or None for utility actions
- heal_range: [min, max] for healing actions, or None
- stat_requirement: Which stat affects this action's effectiveness
- target: Who this action affects (self, single_enemy, all_enemies)
- description: Human-readable description of what it does
- is_defense: Whether this action grants a defensive buff
- defense_reduction: Percentage of incoming damage reduced (for defend)
"""

# --- Base Action Definitions ---
# These are the 5 starter actions every champion has access to.
# NFT skills will extend this list in Phase 7+.

ACTIONS = {
    "basic_strike": {
        "name": "basic_strike",
        "action_point_cost": 1,
        "damage_range": [5, 12],
        "heal_range": None,
        "stat_requirement": "strength",
        "target": "single_enemy",
        "description": "A quick, reliable strike. Low cost, moderate damage.",
        "is_defense": False,
        "defense_reduction": 0.0,
    },
    "heavy_blow": {
        "name": "heavy_blow",
        "action_point_cost": 2,
        "damage_range": [15, 25],
        "heal_range": None,
        "stat_requirement": "strength",
        "target": "single_enemy",
        "description": "A powerful two-handed strike. High damage, high cost.",
        "is_defense": False,
        "defense_reduction": 0.0,
    },
    "defend": {
        "name": "defend",
        "action_point_cost": 1,
        "damage_range": None,
        "heal_range": None,
        "stat_requirement": "endurance",
        "target": "self",
        "description": "Brace for impact. Reduces incoming damage by 30% this turn.",
        "is_defense": True,
        "defense_reduction": 0.30,
    },
    "power_surge": {
        "name": "power_surge",
        "action_point_cost": 3,
        "damage_range": [30, 50],
        "heal_range": None,
        "stat_requirement": "strength",
        "target": "single_enemy",
        "description": "Channel all energy into one devastating attack. Uses entire turn.",
        "is_defense": False,
        "defense_reduction": 0.0,
    },
    "heal": {
        "name": "heal",
        "action_point_cost": 2,
        "damage_range": None,
        "heal_range": [10, 20],
        "stat_requirement": "endurance",
        "target": "self",
        "description": "Recover HP. Amount scales with endurance stat.",
        "is_defense": False,
        "defense_reduction": 0.0,
    },
}


def get_action(action_name: str) -> dict | None:
    """
    Look up an action by name.

    Args:
        action_name: The string key of the action to retrieve.

    Returns:
        The action dictionary if found, or None if the action doesn't exist.
    """
    return ACTIONS.get(action_name)


def get_available_actions() -> list[dict]:
    """
    Return a list of all available actions.
    Used by mock bots and AI bots to see what they can do.

    Returns:
        List of all action dictionaries.
    """
    return list(ACTIONS.values())


def get_affordable_actions(remaining_action_points: int) -> list[dict]:
    """
    Return actions the bot can still afford given remaining action points.

    Args:
        remaining_action_points: How many action points the bot has left this turn.

    Returns:
        List of action dictionaries that cost <= remaining_action_points.
    """
    return [
        action for action in ACTIONS.values()
        if action["action_point_cost"] <= remaining_action_points
    ]
