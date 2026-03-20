"""
mcp/tool_registry.py — Dynamic tool registration for BYTE Wars.

Manages the registry of available combat actions. Starts with the 5 base
actions and supports dynamic registration of new tools (for NFT skills
in Phase 7+).

The registry is the single source of truth for what actions exist.
Both the MCP server and the battle engine read from it.
"""

from copy import deepcopy
from engine.actions import ACTIONS


class ToolRegistry:
    """
    Central registry for all combat actions/tools in BYTE Wars.

    Starts pre-loaded with the 5 base actions. New tools can be registered
    dynamically (e.g., when an NFT skill is equipped on a champion).

    The registry validates tool definitions before accepting them to ensure
    every tool has the required fields for the battle engine.
    """

    # Fields every tool must have to work with the battle engine
    REQUIRED_FIELDS = [
        "name", "action_point_cost", "damage_range", "heal_range",
        "stat_requirement", "target", "description", "is_defense",
        "defense_reduction",
    ]

    def __init__(self):
        """Initialize the registry with the 5 base actions."""
        # Deep copy so modifying the registry doesn't affect the original ACTIONS
        self._tools: dict[str, dict] = deepcopy(ACTIONS)

    def get_tool(self, name: str) -> dict | None:
        """
        Look up a tool by name.

        Args:
            name: The unique identifier of the tool.

        Returns:
            The tool dictionary, or None if not found.
        """
        return self._tools.get(name)

    def get_all_tools(self) -> dict[str, dict]:
        """
        Return all registered tools.

        Returns:
            Dictionary mapping tool names to their definitions.
        """
        return dict(self._tools)

    def get_affordable_tools(self, remaining_ap: int) -> list[dict]:
        """
        Return tools that cost <= the given action points.

        Args:
            remaining_ap: How many action points the bot has left.

        Returns:
            List of tool dictionaries the bot can afford.
        """
        return [
            tool for tool in self._tools.values()
            if tool["action_point_cost"] <= remaining_ap
        ]

    def register_tool(self, tool_def: dict) -> tuple[bool, str]:
        """
        Register a new tool (e.g., an NFT skill).

        Validates the tool definition has all required fields before
        adding it to the registry. Rejects duplicates unless overwrite
        is intended.

        Args:
            tool_def: Dictionary defining the new tool. Must contain
                      all REQUIRED_FIELDS.

        Returns:
            Tuple of (success, error_message). error_message is "" if OK.
        """
        # Validate all required fields are present
        for field in self.REQUIRED_FIELDS:
            if field not in tool_def:
                return False, f"Missing required field: '{field}'"

        name = tool_def["name"]

        # Validate action point cost is 1, 2, or 3
        cost = tool_def["action_point_cost"]
        if cost not in (1, 2, 3):
            return False, f"action_point_cost must be 1, 2, or 3, got {cost}"

        # Validate target type
        valid_targets = ("self", "single_enemy", "all_enemies", "aoe")
        if tool_def["target"] not in valid_targets:
            return False, f"target must be one of {valid_targets}"

        # Validate damage_range format if present
        if tool_def["damage_range"] is not None:
            dr = tool_def["damage_range"]
            if not isinstance(dr, (list, tuple)) or len(dr) != 2:
                return False, "damage_range must be [min, max] or None"
            if dr[0] > dr[1]:
                return False, "damage_range min cannot exceed max"

        # Validate heal_range format if present
        if tool_def["heal_range"] is not None:
            hr = tool_def["heal_range"]
            if not isinstance(hr, (list, tuple)) or len(hr) != 2:
                return False, "heal_range must be [min, max] or None"

        self._tools[name] = deepcopy(tool_def)
        return True, ""

    def unregister_tool(self, name: str) -> tuple[bool, str]:
        """
        Remove a dynamically registered tool.

        Cannot remove base actions — only dynamically added tools.

        Args:
            name: The name of the tool to remove.

        Returns:
            Tuple of (success, error_message).
        """
        # Prevent removing base actions
        if name in ACTIONS:
            return False, f"Cannot remove base action '{name}'"

        if name not in self._tools:
            return False, f"Tool '{name}' not found in registry"

        del self._tools[name]
        return True, ""

    def get_tool_schemas(self) -> list[dict]:
        """
        Return tool schemas formatted for AI bot consumption.

        Each schema includes the fields an AI needs to decide which
        action to use: name, cost, damage/heal range, target type,
        and description.

        Returns:
            List of simplified tool schema dicts.
        """
        schemas = []
        for tool in self._tools.values():
            schema = {
                "name": tool["name"],
                "action_point_cost": tool["action_point_cost"],
                "damage_range": tool["damage_range"],
                "heal_range": tool["heal_range"],
                "target": tool["target"],
                "description": tool["description"],
            }
            schemas.append(schema)
        return schemas
