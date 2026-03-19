"""
engine/turn_manager.py — Pathfinder 2e Action Economy for BYTE Wars.

Manages turn order and action point spending. Each champion gets 3 action
points per turn. Turn order is determined by initiative: endurance stat + d20 roll.

Key rules (from Pathfinder 2e adaptation):
- 3 action points per turn (no banking between turns)
- Each action costs 1, 2, or 3 action points
- A bot cannot spend more than 3 action points per turn
- All action choices are validated before resolution
"""

import random
from dataclasses import dataclass, field


# Maximum action points each champion gets per turn
MAX_ACTION_POINTS = 3

# Initiative roll uses a d20 (1-20)
INITIATIVE_DIE = 20


@dataclass
class TurnOrder:
    """
    Represents the initiative order for a match.

    Each entry maps a champion ID to their initiative score.
    Higher initiative goes first.
    """
    order: list[tuple[str, int]] = field(default_factory=list)

    def get_ordered_ids(self) -> list[str]:
        """Return champion IDs sorted by initiative (highest first)."""
        return [champion_id for champion_id, _ in self.order]


class TurnManager:
    """
    Manages the Pathfinder 2e-style action economy for BYTE Wars battles.

    Responsibilities:
    - Roll initiative for all champions at match start
    - Track action points per turn
    - Validate that chosen actions don't exceed the 3 AP budget
    - Determine turn order each round
    """

    def roll_initiative(self, champions: list[dict]) -> TurnOrder:
        """
        Roll initiative for all champions to determine turn order.

        Initiative = endurance stat + random d20 roll.
        Higher scores go first. Ties broken randomly.

        Args:
            champions: List of champion dicts with at least 'id' and 'stats'.

        Returns:
            TurnOrder with champions sorted by initiative score (highest first).
        """
        initiatives = []
        for champ in champions:
            # Endurance stat contributes to initiative (you're more alert)
            endurance = champ["stats"].get("endurance", 50)

            # Roll a d20 for randomness
            roll = random.randint(1, INITIATIVE_DIE)

            # Total initiative score
            initiative_score = endurance + roll
            initiatives.append((champ["id"], initiative_score))

        # Sort by initiative score descending (highest goes first)
        # Ties are broken by random shuffle (Python's sort is stable,
        # so we shuffle first then sort)
        random.shuffle(initiatives)
        initiatives.sort(key=lambda x: x[1], reverse=True)

        return TurnOrder(order=initiatives)

    def validate_actions(
        self, chosen_actions: list[dict], available_actions: dict
    ) -> tuple[bool, str]:
        """
        Validate that a list of chosen actions is legal.

        Rules:
        1. Total action point cost must not exceed MAX_ACTION_POINTS (3)
        2. Every action must exist in the available actions set
        3. At least one action must be chosen

        Args:
            chosen_actions: List of action dicts the bot wants to perform.
            available_actions: Dict of all legal actions {name: action_dict}.

        Returns:
            Tuple of (is_valid, error_message). error_message is "" if valid.
        """
        if not chosen_actions:
            return False, "No actions chosen. Must choose at least one action."

        total_cost = 0
        for action in chosen_actions:
            action_name = action.get("name", "")

            # Check the action actually exists
            if action_name not in available_actions:
                return False, f"Unknown action: '{action_name}'"

            # Accumulate action point cost
            total_cost += available_actions[action_name]["action_point_cost"]

        # Check total doesn't exceed the 3 AP budget
        if total_cost > MAX_ACTION_POINTS:
            return (
                False,
                f"Action cost {total_cost} exceeds max {MAX_ACTION_POINTS} action points."
            )

        return True, ""

    def get_action_points_remaining(
        self, used_actions: list[dict], available_actions: dict
    ) -> int:
        """
        Calculate how many action points remain after the given actions.

        Args:
            used_actions: Actions already taken this turn.
            available_actions: Dict of all legal actions.

        Returns:
            Number of action points still available (0-3).
        """
        spent = sum(
            available_actions[a["name"]]["action_point_cost"]
            for a in used_actions
            if a["name"] in available_actions
        )
        return max(MAX_ACTION_POINTS - spent, 0)
