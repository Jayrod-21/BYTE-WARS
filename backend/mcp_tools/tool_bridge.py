"""
mcp/tool_bridge.py — Bridge between MCP tool calls and the Battle Engine.

This is the connector layer that translates MCP tool call results into
battle engine actions. When a bot calls an MCP tool (e.g., basic_strike),
the bridge:

1. Receives the tool call result (action name + target)
2. Looks up the full action definition from the ToolRegistry
3. Passes it to the DamageResolver for probabilistic resolution
4. Returns the resolution result to the battle engine

This bridge allows the battle engine to work the same whether actions
come from MCP tool calls (Phase 2+) or direct dict lookups (Phase 1).
"""

from engine.damage_resolver import DamageResolver, ResolutionResult
from mcp_tools.tool_registry import ToolRegistry


class ToolBridge:
    """
    Bridges MCP tool calls to battle engine resolution.

    Sits between the MCP tool server and the DamageResolver.
    Takes a tool call result and resolves it into concrete damage/healing.
    """

    def __init__(self, registry: ToolRegistry | None = None):
        """
        Args:
            registry: ToolRegistry to look up action definitions.
                      Creates a default one if not provided.
        """
        self.registry = registry or ToolRegistry()
        self.resolver = DamageResolver()

    def resolve_tool_call(
        self,
        tool_call: dict,
        attacker_id: str,
        attacker_stats: dict,
        target_id: str,
        target_stats: dict,
        target_hp: float,
        target_max_hp: float,
        target_is_defending: bool = False,
    ) -> ResolutionResult | None:
        """
        Resolve a single MCP tool call into a battle outcome.

        Args:
            tool_call: Dict with 'action' key (the tool/action name).
            attacker_id: ID of the champion using the tool.
            attacker_stats: Attacker's stats dict (strength, endurance, etc.).
            target_id: ID of the target champion.
            target_stats: Target's stats dict.
            target_hp: Target's current HP.
            target_max_hp: Target's maximum HP.
            target_is_defending: Whether the target used 'defend' this turn.

        Returns:
            ResolutionResult with damage/healing details, or None if
            the action couldn't be resolved.
        """
        action_name = tool_call.get("action", "")
        action_def = self.registry.get_tool(action_name)

        if action_def is None:
            return None

        # --- Route to the correct resolver method based on action type ---

        if action_def["is_defense"]:
            # Defend action — sets a flag, no damage
            result = self.resolver.resolve_defend(attacker_id, target_hp)
            return result

        elif action_def["heal_range"] is not None:
            # Heal action — restore HP to self
            result = self.resolver.resolve_heal(
                action_def,
                attacker_stats,
                target_hp,
                target_max_hp,
            )
            result.attacker_id = attacker_id
            result.target_id = attacker_id  # Heals always target self
            return result

        elif action_def["damage_range"] is not None:
            # Attack action — deal damage to target
            result = self.resolver.resolve_attack(
                action_def,
                attacker_stats,
                target_stats,
                target_hp,
                target_is_defending,
            )
            result.attacker_id = attacker_id
            result.target_id = target_id
            return result

        return None

    def get_available_tools(self) -> dict[str, dict]:
        """Return all available tools from the registry."""
        return self.registry.get_all_tools()

    def get_tool_schemas(self) -> list[dict]:
        """Return tool schemas formatted for bot consumption."""
        return self.registry.get_tool_schemas()
