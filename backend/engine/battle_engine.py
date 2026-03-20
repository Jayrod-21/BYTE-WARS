"""
engine/battle_engine.py — Core Battle Engine loop for BYTE Wars.

Runs a complete match between 2-4 champions. The engine:
1. Rolls initiative to determine turn order
2. Each turn: every living champion picks actions (mock bot or MCP tool calls)
3. Actions are validated via BotResponseParser, then resolved via ToolBridge
4. Match ends when one champion remains or the turn limit (50) is hit
5. Returns a BattleHistory with every turn logged for playback

Phase 2 update: Now uses ToolBridge for resolution and BotResponseParser for
validation. GameState is built each turn for bot context. MockBot updated to
receive game state. Falls back to Phase 1 direct mode if MCP modules unavailable.
"""

import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from engine.actions import ACTIONS, get_affordable_actions
from engine.damage_resolver import DamageResolver, ResolutionResult
from engine.turn_manager import TurnManager, MAX_ACTION_POINTS
from mcp_tools.tool_registry import ToolRegistry
from mcp_tools.tool_bridge import ToolBridge
from mcp_tools.game_state import build_game_state
from mcp_tools.bot_response import BotResponseParser


# Maximum turns before the match is declared timed out
TURN_LIMIT = 50


@dataclass
class BattleChampion:
    """
    Runtime state of a champion during a battle.
    Separate from the DB model — this tracks HP, buffs, and match state.
    """
    id: str
    name: str
    stats: dict
    max_hp: float
    current_hp: float
    is_alive: bool = True
    is_defending: bool = False  # Reset each turn, set when 'defend' is used

    @classmethod
    def from_dict(cls, champion_dict: dict) -> "BattleChampion":
        """Create a BattleChampion from a champion data dictionary."""
        hp = champion_dict["stats"]["health"]
        return cls(
            id=str(champion_dict.get("id", uuid.uuid4())),
            name=champion_dict["name"],
            stats=dict(champion_dict["stats"]),
            max_hp=float(hp),
            current_hp=float(hp),
        )


@dataclass
class TurnEntry:
    """A single turn's worth of actions and resolutions for the battle log."""
    turn_number: int
    champion_id: str
    champion_name: str
    actions_taken: list[dict] = field(default_factory=list)
    resolutions: list[dict] = field(default_factory=list)
    game_state_snapshot: dict = field(default_factory=dict)
    used_fallback: bool = False


@dataclass
class BattleHistory:
    """
    Complete record of a battle, from start to finish.
    This is what gets stored in the Match model and passed to the playback renderer.
    """
    match_id: str
    champion_ids: list[str]
    champion_names: list[str]
    winner_id: str | None = None
    winner_name: str | None = None
    status: str = "pending"  # pending → active → complete | timed_out
    total_turns: int = 0
    turns: list[dict] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self) -> dict:
        """Convert to a plain dictionary for JSON serialization."""
        return asdict(self)


class MockBot:
    """
    A mock bot that randomly selects actions each turn.

    Phase 2 update: Now receives a GameState object for context and uses
    the BotResponseParser format. Still picks randomly, but validates
    through the same pipeline as real AI bots will in Phase 4.
    """

    def choose_actions(
        self,
        champion: BattleChampion,
        opponents: list[BattleChampion],
        available_actions: dict,
        game_state=None,
    ) -> list[dict]:
        """
        Randomly select actions up to the 3 action point budget.

        Args:
            champion: The bot's current battle state.
            opponents: List of living opponents.
            available_actions: Dict of all available actions.
            game_state: Optional GameState object (used by AI bots in Phase 4).

        Returns:
            List of action dicts with 'action' and 'target_id' keys.
        """
        chosen = []
        remaining_ap = MAX_ACTION_POINTS

        while remaining_ap > 0:
            # Get actions we can still afford
            affordable = [
                a for a in available_actions.values()
                if a["action_point_cost"] <= remaining_ap
            ]
            if not affordable:
                break

            # Pick a random action
            action = random.choice(affordable)
            action_entry = {"action": action["name"]}

            # Assign a target if the action targets an enemy
            if action["target"] == "single_enemy":
                living_opponents = [o for o in opponents if o.is_alive]
                if not living_opponents:
                    break
                target = random.choice(living_opponents)
                action_entry["target_id"] = target.id
            elif action["target"] == "self":
                action_entry["target_id"] = champion.id

            chosen.append(action_entry)
            remaining_ap -= action["action_point_cost"]

        return chosen


class BattleEngine:
    """
    The core battle engine. Runs a complete match between 2-4 champions.

    Phase 2 update: Now uses:
    - ToolRegistry: Single source of truth for available actions
    - ToolBridge: Connects MCP tool calls to the DamageResolver
    - GameState: Built each turn and passed to bots for decision-making
    - BotResponseParser: Validates bot responses before resolution

    Flow:
    1. Initialize battle state from champion data
    2. Roll initiative for turn order
    3. Loop turns until one champion remains or turn limit hit
    4. Each turn: build game state → bot picks actions → parse/validate →
       resolve via ToolBridge → log results
    5. Return complete BattleHistory
    """

    def __init__(self, tool_registry: ToolRegistry | None = None):
        """
        Args:
            tool_registry: Optional custom ToolRegistry. If not provided,
                          creates a default one with the 5 base actions.
        """
        self.registry = tool_registry or ToolRegistry()
        self.bridge = ToolBridge(self.registry)
        self.turn_manager = TurnManager()
        self.parser = BotResponseParser(self.registry)
        self.mock_bot = MockBot()

    def run_battle(self, champions_data: list[dict]) -> BattleHistory:
        """
        Run a complete battle between 2-4 champions.

        Args:
            champions_data: List of champion dictionaries, each containing
                            at minimum 'id', 'name', and 'stats'.

        Returns:
            BattleHistory with every turn logged, winner determined.

        Raises:
            ValueError: If fewer than 2 or more than 4 champions provided.
        """
        # --- Validate participant count ---
        if len(champions_data) < 2 or len(champions_data) > 4:
            raise ValueError(
                f"Battle requires 2-4 champions, got {len(champions_data)}"
            )

        # --- Initialize battle state ---
        match_id = str(uuid.uuid4())
        fighters = [BattleChampion.from_dict(c) for c in champions_data]
        all_tools = self.registry.get_all_tools()
        tool_schemas = self.registry.get_tool_schemas()

        history = BattleHistory(
            match_id=match_id,
            champion_ids=[f.id for f in fighters],
            champion_names=[f.name for f in fighters],
            status="active",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # --- Roll initiative to determine turn order ---
        initiative_order = self.turn_manager.roll_initiative(champions_data)
        ordered_ids = initiative_order.get_ordered_ids()

        # --- Main battle loop ---
        for turn_number in range(1, TURN_LIMIT + 1):
            history.total_turns = turn_number

            # Reset defense buffs at the start of each round
            for fighter in fighters:
                fighter.is_defending = False

            # Each champion takes their turn in initiative order
            for champion_id in ordered_ids:
                # Find this champion in the fighters list
                champion = next(
                    (f for f in fighters if f.id == champion_id), None
                )
                if champion is None or not champion.is_alive:
                    continue

                # Get living opponents
                opponents = [
                    f for f in fighters if f.is_alive and f.id != champion_id
                ]
                if not opponents:
                    break  # This champion is the last one standing

                # --- Build game state for this bot's turn ---
                game_state = build_game_state(
                    turn_number=turn_number,
                    champion=champion,
                    opponents=[f for f in fighters if f.id != champion_id],
                    tool_schemas=tool_schemas,
                    recent_history=history.turns[-6:],  # Last few entries
                    total_champions=len(fighters),
                )

                # --- Bot chooses actions (mock bot for now) ---
                raw_response = self.mock_bot.choose_actions(
                    champion, opponents, all_tools, game_state
                )

                # --- Parse and validate through BotResponseParser ---
                alive_opponent_ids = [o.id for o in opponents if o.is_alive]
                parse_result = self.parser.parse(
                    raw_response, champion_id, alive_opponent_ids
                )

                # Convert parsed actions to engine format
                chosen_actions = self.parser.actions_to_engine_format(
                    parse_result.actions
                )

                # --- Resolve each action via ToolBridge ---
                turn_entry = TurnEntry(
                    turn_number=turn_number,
                    champion_id=champion_id,
                    champion_name=champion.name,
                    used_fallback=parse_result.used_fallback,
                )

                for action_choice in chosen_actions:
                    action_name = action_choice["name"]
                    action_def = self.registry.get_tool(action_name)
                    if action_def is None:
                        continue

                    target_id = action_choice.get("target_id", champion_id)

                    # Record the action taken
                    turn_entry.actions_taken.append({
                        "action": action_name,
                        "target_id": target_id,
                        "cost": action_def["action_point_cost"],
                    })

                    # --- Resolve via ToolBridge ---
                    if action_def["is_defense"]:
                        # Defend: set flag and resolve
                        champion.is_defending = True
                        result = self.bridge.resolve_tool_call(
                            {"action": action_name},
                            attacker_id=champion_id,
                            attacker_stats=champion.stats,
                            target_id=champion_id,
                            target_stats=champion.stats,
                            target_hp=champion.current_hp,
                            target_max_hp=champion.max_hp,
                        )

                    elif action_def["heal_range"] is not None:
                        # Heal: resolve and apply
                        result = self.bridge.resolve_tool_call(
                            {"action": action_name},
                            attacker_id=champion_id,
                            attacker_stats=champion.stats,
                            target_id=champion_id,
                            target_stats=champion.stats,
                            target_hp=champion.current_hp,
                            target_max_hp=champion.max_hp,
                        )
                        if result:
                            champion.current_hp = result.target_hp_after

                    elif action_def["damage_range"] is not None:
                        # Attack: find target, resolve, apply
                        target = next(
                            (f for f in fighters if f.id == target_id), None
                        )
                        if target is None or not target.is_alive:
                            continue

                        result = self.bridge.resolve_tool_call(
                            {"action": action_name},
                            attacker_id=champion_id,
                            attacker_stats=champion.stats,
                            target_id=target_id,
                            target_stats=target.stats,
                            target_hp=target.current_hp,
                            target_max_hp=target.max_hp,
                            target_is_defending=target.is_defending,
                        )
                        if result:
                            target.current_hp = result.target_hp_after
                            if result.is_kill:
                                target.is_alive = False
                    else:
                        continue

                    # Log the resolution
                    if result:
                        turn_entry.resolutions.append({
                            "action": result.action_name,
                            "attacker_id": result.attacker_id,
                            "target_id": result.target_id,
                            "raw_roll": result.raw_roll,
                            "modified_damage": result.modified_damage,
                            "healing_done": result.healing_done,
                            "target_hp_before": result.target_hp_before,
                            "target_hp_after": result.target_hp_after,
                            "is_kill": result.is_kill,
                        })

                # Add this turn's entry to history
                history.turns.append(asdict(turn_entry))

            # --- Check win condition ---
            alive = [f for f in fighters if f.is_alive]

            if len(alive) == 1:
                # We have a winner!
                history.winner_id = alive[0].id
                history.winner_name = alive[0].name
                history.status = "complete"
                history.ended_at = datetime.now(timezone.utc).isoformat()
                return history

            if len(alive) == 0:
                # Everyone died in the same turn (unlikely but possible)
                history.status = "complete"
                history.winner_id = None
                history.winner_name = None
                history.ended_at = datetime.now(timezone.utc).isoformat()
                return history

        # --- Turn limit exceeded ---
        history.status = "timed_out"
        history.winner_id = None
        history.winner_name = None
        history.ended_at = datetime.now(timezone.utc).isoformat()
        return history
