"""
mcp/tool_server.py — MCP Tool Server for BYTE Wars.

Creates a FastMCP server that exposes combat actions as MCP tools.
Each of the 5 base actions is registered as a callable tool with proper
schemas describing cost, damage range, and targeting.

The MCP server can run standalone (for AI model integration) or be
accessed programmatically via the ToolBridge for in-process resolution.

Key concepts:
- Each tool takes a target_id parameter (who to attack/heal)
- Tools return a result dict describing what happened
- The actual damage resolution still goes through the DamageResolver
- This layer translates between MCP protocol and battle engine internals
"""

from mcp.server.fastmcp import FastMCP

from engine.actions import ACTIONS


def create_mcp_server() -> FastMCP:
    """
    Create and configure the BYTE Wars MCP tool server.

    Registers all 5 base combat actions as MCP tools with proper
    descriptions and parameter schemas.

    Returns:
        Configured FastMCP server instance ready to run or be queried.
    """
    server = FastMCP(
        name="byte-wars-tools",
        instructions=(
            "BYTE Wars Combat Tool Server. "
            "You are a champion in the BYTE Wars arena. "
            "Use these tools to fight your opponents. "
            "You have 3 action points per turn. Choose wisely."
        ),
    )

    # --- Register each base action as an MCP tool ---
    # We use server.add_tool() for dynamic registration rather than decorators,
    # so the same pattern works for NFT skills added at runtime.

    @server.tool(
        name="basic_strike",
        description=(
            "A quick, reliable strike. Cost: 1 AP. Damage: 5-12. "
            "Requires strength. Target: single enemy. "
            "Good for using leftover action points."
        ),
    )
    async def basic_strike(target_id: str) -> dict:
        """
        Strike a single enemy for 5-12 base damage.

        Args:
            target_id: The ID of the enemy champion to attack.

        Returns:
            Dict confirming the action was queued for resolution.
        """
        return {
            "action": "basic_strike",
            "target_id": target_id,
            "action_point_cost": 1,
            "damage_range": [5, 12],
            "status": "queued",
        }

    @server.tool(
        name="heavy_blow",
        description=(
            "A powerful two-handed strike. Cost: 2 AP. Damage: 15-25. "
            "Requires strength. Target: single enemy. "
            "High damage but uses most of your turn."
        ),
    )
    async def heavy_blow(target_id: str) -> dict:
        """
        Strike a single enemy for 15-25 base damage.

        Args:
            target_id: The ID of the enemy champion to attack.

        Returns:
            Dict confirming the action was queued for resolution.
        """
        return {
            "action": "heavy_blow",
            "target_id": target_id,
            "action_point_cost": 2,
            "damage_range": [15, 25],
            "status": "queued",
        }

    @server.tool(
        name="defend",
        description=(
            "Brace for impact. Cost: 1 AP. No damage. "
            "Reduces ALL incoming damage by 30%% for this turn. "
            "Target: self. Good when low on HP."
        ),
    )
    async def defend(target_id: str = "self") -> dict:
        """
        Activate defensive stance, reducing incoming damage by 30%.

        Args:
            target_id: Should be 'self' or your own champion ID.

        Returns:
            Dict confirming the defense was queued.
        """
        return {
            "action": "defend",
            "target_id": target_id,
            "action_point_cost": 1,
            "damage_range": None,
            "defense_reduction": 0.30,
            "status": "queued",
        }

    @server.tool(
        name="power_surge",
        description=(
            "Channel all energy into one devastating attack. Cost: 3 AP. "
            "Damage: 30-50. Requires strength + endurance. "
            "Target: single enemy. Uses your ENTIRE turn."
        ),
    )
    async def power_surge(target_id: str) -> dict:
        """
        Unleash a devastating attack for 30-50 base damage. Uses all 3 AP.

        Args:
            target_id: The ID of the enemy champion to attack.

        Returns:
            Dict confirming the action was queued for resolution.
        """
        return {
            "action": "power_surge",
            "target_id": target_id,
            "action_point_cost": 3,
            "damage_range": [30, 50],
            "status": "queued",
        }

    @server.tool(
        name="heal",
        description=(
            "Recover HP. Cost: 2 AP. Heals: 10-20 HP. "
            "Requires endurance. Target: self. "
            "Amount scales with your endurance stat."
        ),
    )
    async def heal(target_id: str = "self") -> dict:
        """
        Heal yourself for 10-20 base HP.

        Args:
            target_id: Should be 'self' or your own champion ID.

        Returns:
            Dict confirming the heal was queued.
        """
        return {
            "action": "heal",
            "target_id": target_id,
            "action_point_cost": 2,
            "heal_range": [10, 20],
            "status": "queued",
        }

    return server


def register_nft_tool(server: FastMCP, tool_def: dict) -> None:
    """
    Dynamically register an NFT skill as an MCP tool on the server.

    This is used in Phase 7+ when champions equip NFT skills that add
    new combat actions beyond the base 5.

    Args:
        server: The FastMCP server instance.
        tool_def: Tool definition dict from the ToolRegistry.
    """
    name = tool_def["name"]
    cost = tool_def["action_point_cost"]
    desc = tool_def["description"]

    # Build a description string with cost and range info
    if tool_def.get("damage_range"):
        dr = tool_def["damage_range"]
        full_desc = f"{desc} Cost: {cost} AP. Damage: {dr[0]}-{dr[1]}."
    elif tool_def.get("heal_range"):
        hr = tool_def["heal_range"]
        full_desc = f"{desc} Cost: {cost} AP. Heals: {hr[0]}-{hr[1]} HP."
    else:
        full_desc = f"{desc} Cost: {cost} AP."

    # Create the tool function dynamically
    async def nft_tool_fn(target_id: str) -> dict:
        return {
            "action": name,
            "target_id": target_id,
            "action_point_cost": cost,
            "damage_range": tool_def.get("damage_range"),
            "heal_range": tool_def.get("heal_range"),
            "status": "queued",
        }

    # Register it on the server
    server.add_tool(
        nft_tool_fn,
        name=name,
        description=full_desc,
    )
