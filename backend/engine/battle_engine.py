"""
engine/battle_engine.py — Core Battle Engine loop for BYTE Wars.

Runs a complete match between 2-4 champions. The engine:
1. Rolls initiative to determine turn order
2. Each turn: every living champion picks actions (mock bot = random)
3. Actions are validated, then resolved via DamageResolver
4. Match ends when one champion remains or the turn limit (50) is hit
5. Returns a BattleHistory with every turn logged for playback

This is the heart of BYTE Wars. All battles resolve fully before visualization.
"""

import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from engine.actions import ACTIONS, get_affordable_actions
from engine.damage_resolver import DamageResolver, ResolutionResult
from engine.turn_manager import TurnManager, MAX_ACTION_POINTS


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

    Used for Phase 1 testing. In Phase 4, this is replaced by real AI model
    calls where the bot receives game state and chooses actions via MCP tools.
    """

    def choose_actions(
        self,
        champion: BattleChampion,
        opponents: list[BattleChampion],
        available_actions: dict,
    ) -> list[dict]:
        """
        Randomly select actions up to the 3 action point budget.

        Strategy: Keep picking random affordable actions until action points
        are exhausted or no more affordable actions remain.

        Args:
            champion: The bot's current battle state.
            opponents: List of living opponents.
            available_actions: Dict of all available actions.

        Returns:
            List of action dicts with 'name' and 'target_id' keys.
        """
        chosen = []
        remaining_ap = MAX_ACTION_POINTS

        while remaining_ap > 0:
            # Get actions we can still afford
            affordable = get_affordable_actions(remaining_ap)
            if not affordable:
                break

            # Pick a random action
            action = random.choice(affordable)
            action_entry = {"name": action["name"]}

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

    Flow:
    1. Initialize battle state from champion data
    2. Roll initiative for turn order
    3. Loop turns until one champion remains or turn limit hit
    4. Each turn: bot picks actions → validate → resolve → log
    5. Return complete BattleHistory
    """

    def __init__(self):
        self.turn_manager = TurnManager()
        self.damage_resolver = DamageResolver()
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

                # --- Bot chooses actions ---
                chosen_actions = self.mock_bot.choose_actions(
                    champion, opponents, ACTIONS
                )

                # --- Validate actions ---
                is_valid, error = self.turn_manager.validate_actions(
                    chosen_actions, ACTIONS
                )
                if not is_valid:
                    # If invalid (shouldn't happen with mock bot), use a basic strike
                    living_opponents = [o for o in opponents if o.is_alive]
                    if living_opponents:
                        chosen_actions = [{
                            "name": "basic_strike",
                            "target_id": living_opponents[0].id
                        }]
                    else:
                        chosen_actions = []

                # --- Resolve each action ---
                turn_entry = TurnEntry(
                    turn_number=turn_number,
                    champion_id=champion_id,
                    champion_name=champion.name,
                )

                for action_choice in chosen_actions:
                    action_def = ACTIONS.get(action_choice["name"])
                    if action_def is None:
                        continue

                    target_id = action_choice.get("target_id", champion_id)

                    # Record the action taken
                    turn_entry.actions_taken.append({
                        "action": action_choice["name"],
                        "target_id": target_id,
                        "cost": action_def["action_point_cost"],
                    })

                    # --- Resolve based on action type ---
                    if action_def["is_defense"]:
                        # Defend: set the defending flag
                        champion.is_defending = True
                        result = self.damage_resolver.resolve_defend(
                            champion_id, champion.current_hp
                        )

                    elif action_def["heal_range"] is not None:
                        # Heal: restore HP to self
                        result = self.damage_resolver.resolve_heal(
                            action_def,
                            champion.stats,
                            champion.current_hp,
                            champion.max_hp,
                        )
                        result.attacker_id = champion_id
                        result.target_id = champion_id
                        # Apply healing
                        champion.current_hp = result.target_hp_after

                    elif action_def["damage_range"] is not None:
                        # Attack: deal damage to target
                        target = next(
                            (f for f in fighters if f.id == target_id), None
                        )
                        if target is None or not target.is_alive:
                            continue

                        result = self.damage_resolver.resolve_attack(
                            action_def,
                            champion.stats,
                            target.stats,
                            target.current_hp,
                            target.is_defending,
                        )
                        result.attacker_id = champion_id
                        result.target_id = target_id

                        # Apply damage
                        target.current_hp = result.target_hp_after
                        if result.is_kill:
                            target.is_alive = False
                    else:
                        continue

                    # Log the resolution
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
