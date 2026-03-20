"""
mcp/game_state.py — Game state object for BYTE Wars.

Builds the game state that each bot receives at the start of their turn.
The game state includes:
- The bot's own stats (HP, strength, endurance, buffs)
- All opponents' visible stats (HP, name, archetype — not their strategy)
- Available MCP tools and their costs
- Current turn number and remaining action points
- Recent turn history (last 3 turns for context)

This is what gets passed to the AI model so it can make informed decisions.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class OpponentState:
    """
    What a bot can see about an opponent.
    Does NOT include the opponent's system prompt or strategy.
    """
    id: str
    name: str
    current_hp: float
    max_hp: float
    is_alive: bool
    is_defending: bool  # Visible — you can see someone bracing


@dataclass
class SelfState:
    """What a bot knows about itself."""
    id: str
    name: str
    current_hp: float
    max_hp: float
    stats: dict  # Full stats (health, strength, endurance)
    is_defending: bool


@dataclass
class GameState:
    """
    The complete game state sent to a bot at the start of its turn.

    This is the bot's "eyes" — everything it can see about the battle.
    The AI model uses this to decide which actions to take.
    """
    # Current turn info
    turn_number: int
    action_points_remaining: int  # Always 3 at start of turn

    # Self state — full details about the bot's own champion
    self_state: dict = field(default_factory=dict)

    # Opponents — what the bot can see about each enemy
    opponents: list[dict] = field(default_factory=list)

    # Available tools — what actions the bot can take
    available_tools: list[dict] = field(default_factory=list)

    # Recent history — last 3 turns of actions for tactical context
    recent_history: list[dict] = field(default_factory=list)

    # Match metadata
    total_champions: int = 0
    champions_alive: int = 0

    def to_dict(self) -> dict:
        """Convert to a plain dictionary for JSON serialization."""
        return asdict(self)

    def to_prompt(self) -> str:
        """
        Convert the game state to a human-readable prompt string.

        This is what gets injected into the AI model's context so it
        can understand the current battle situation and choose actions.
        """
        lines = [
            f"=== BATTLE STATE (Turn {self.turn_number}) ===",
            f"Action Points Available: {self.action_points_remaining}",
            "",
            "--- YOUR CHAMPION ---",
            f"Name: {self.self_state.get('name', 'Unknown')}",
            f"HP: {self.self_state.get('current_hp', 0)}/{self.self_state.get('max_hp', 0)}",
            f"Strength: {self.self_state.get('stats', {}).get('strength', 0)}",
            f"Endurance: {self.self_state.get('stats', {}).get('endurance', 0)}",
            f"Defending: {'Yes' if self.self_state.get('is_defending') else 'No'}",
            "",
            f"--- OPPONENTS ({self.champions_alive - 1} alive) ---",
        ]

        for opp in self.opponents:
            if opp.get("is_alive", False):
                status = "DEFENDING" if opp.get("is_defending") else "active"
                lines.append(
                    f"  {opp['name']} [{opp['id'][:8]}]: "
                    f"HP {opp['current_hp']}/{opp['max_hp']} ({status})"
                )

        lines.append("")
        lines.append("--- AVAILABLE ACTIONS ---")
        for tool in self.available_tools:
            cost = tool["action_point_cost"]
            if tool.get("damage_range"):
                effect = f"damage {tool['damage_range'][0]}-{tool['damage_range'][1]}"
            elif tool.get("heal_range"):
                effect = f"heal {tool['heal_range'][0]}-{tool['heal_range'][1]}"
            else:
                effect = "utility"
            lines.append(
                f"  {tool['name']} (cost: {cost} AP, {effect}, target: {tool['target']})"
            )
            lines.append(f"    {tool['description']}")

        if self.recent_history:
            lines.append("")
            lines.append("--- RECENT ACTIONS (last 3 turns) ---")
            for entry in self.recent_history[-3:]:
                champ = entry.get("champion_name", "Unknown")
                actions = entry.get("actions_taken", [])
                for a in actions:
                    lines.append(f"  {champ} used {a.get('action', '?')}")

        lines.append("")
        lines.append(
            "Choose your actions. You have 3 action points. "
            "Respond with a JSON array of actions, each with 'action' and 'target_id'."
        )

        return "\n".join(lines)


def build_game_state(
    turn_number: int,
    champion,  # BattleChampion
    opponents: list,  # list[BattleChampion]
    tool_schemas: list[dict],
    recent_history: list[dict],
    total_champions: int,
) -> GameState:
    """
    Build a GameState object for a bot's turn.

    Args:
        turn_number: Current turn number in the match.
        champion: The BattleChampion whose turn it is.
        opponents: List of all other BattleChampions (alive or dead).
        tool_schemas: Available tool schemas from the ToolRegistry.
        recent_history: Last few turns of battle history.
        total_champions: Total number of champions in the match.

    Returns:
        GameState ready to be sent to the AI bot or converted to a prompt.
    """
    # Build self state
    self_state = {
        "id": champion.id,
        "name": champion.name,
        "current_hp": champion.current_hp,
        "max_hp": champion.max_hp,
        "stats": champion.stats,
        "is_defending": champion.is_defending,
    }

    # Build opponent states (only reveal visible info)
    opp_states = []
    for opp in opponents:
        opp_states.append({
            "id": opp.id,
            "name": opp.name,
            "current_hp": opp.current_hp,
            "max_hp": opp.max_hp,
            "is_alive": opp.is_alive,
            "is_defending": opp.is_defending,
        })

    champions_alive = sum(1 for o in opponents if o.is_alive) + 1  # +1 for self

    return GameState(
        turn_number=turn_number,
        action_points_remaining=3,
        self_state=self_state,
        opponents=opp_states,
        available_tools=tool_schemas,
        recent_history=recent_history[-3:] if recent_history else [],
        total_champions=total_champions,
        champions_alive=champions_alive,
    )
