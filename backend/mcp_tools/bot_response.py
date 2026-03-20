"""
mcp/bot_response.py — Bot response parsing and validation for BYTE Wars.

When an AI bot (or mock bot) chooses actions, the response needs to be parsed
and validated before the battle engine can resolve it. This module handles:

1. Parsing the bot's response (JSON array of actions)
2. Validating each action exists in the tool registry
3. Checking total action point cost doesn't exceed 3
4. Ensuring targets are valid (alive opponents for attacks, self for heals)
5. Returning a clean, validated action list or falling back to a default action

If validation fails, the bot gets a fallback action (basic_strike on a random
opponent) so the match can continue without crashing.
"""

import json
import random
from dataclasses import dataclass


@dataclass
class ParsedAction:
    """A single validated action from a bot's response."""
    action_name: str
    target_id: str
    action_point_cost: int


@dataclass
class ParseResult:
    """Result of parsing and validating a bot's response."""
    success: bool
    actions: list[ParsedAction]
    errors: list[str]
    used_fallback: bool = False


class BotResponseParser:
    """
    Parses and validates bot action responses.

    Accepts either a JSON string or a Python list of action dicts.
    Each action must have an 'action' (or 'name') field and a 'target_id' field.

    Validation rules:
    - Every action must exist in the tool registry
    - Total AP cost cannot exceed 3
    - Attack targets must be alive opponents
    - Self-targeting actions must target the bot itself
    """

    def __init__(self, tool_registry):
        """
        Args:
            tool_registry: ToolRegistry instance with available actions.
        """
        self.registry = tool_registry

    def parse(
        self,
        response: str | list,
        champion_id: str,
        alive_opponent_ids: list[str],
    ) -> ParseResult:
        """
        Parse and validate a bot's action response.

        Args:
            response: Either a JSON string or a list of action dicts.
                      Each dict should have 'action' (str) and 'target_id' (str).
            champion_id: The ID of the bot making the choices.
            alive_opponent_ids: IDs of living opponents (valid attack targets).

        Returns:
            ParseResult with validated actions, or errors + fallback actions.
        """
        errors = []

        # Step 1: Parse JSON if string
        if isinstance(response, str):
            try:
                action_list = json.loads(response)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON response: {e}")
                return self._fallback(champion_id, alive_opponent_ids, errors)
        elif isinstance(response, list):
            action_list = response
        else:
            errors.append(f"Expected list or JSON string, got {type(response).__name__}")
            return self._fallback(champion_id, alive_opponent_ids, errors)

        # Step 2: Validate it's a list
        if not isinstance(action_list, list):
            errors.append("Response must be a JSON array of actions")
            return self._fallback(champion_id, alive_opponent_ids, errors)

        if len(action_list) == 0:
            errors.append("No actions provided")
            return self._fallback(champion_id, alive_opponent_ids, errors)

        # Step 3: Validate each action
        parsed_actions = []
        total_ap = 0

        for i, action_dict in enumerate(action_list):
            if not isinstance(action_dict, dict):
                errors.append(f"Action {i}: expected dict, got {type(action_dict).__name__}")
                continue

            # Accept 'action' or 'name' as the action key
            action_name = action_dict.get("action") or action_dict.get("name", "")
            target_id = action_dict.get("target_id", "")

            # Check action exists in registry
            tool = self.registry.get_tool(action_name)
            if tool is None:
                errors.append(f"Action {i}: unknown action '{action_name}'")
                continue

            # Check AP budget
            cost = tool["action_point_cost"]
            if total_ap + cost > 3:
                errors.append(
                    f"Action {i}: '{action_name}' (cost {cost}) would exceed "
                    f"3 AP budget (already spent {total_ap})"
                )
                continue

            # Validate targeting
            if tool["target"] == "single_enemy":
                if target_id not in alive_opponent_ids:
                    # Auto-assign a random alive opponent if target is invalid
                    if alive_opponent_ids:
                        target_id = random.choice(alive_opponent_ids)
                    else:
                        errors.append(f"Action {i}: no alive opponents to target")
                        continue
            elif tool["target"] == "self":
                # Self-targeting actions always target the champion itself
                target_id = champion_id

            parsed_actions.append(ParsedAction(
                action_name=action_name,
                target_id=target_id,
                action_point_cost=cost,
            ))
            total_ap += cost

        # If no valid actions survived validation, use fallback
        if not parsed_actions:
            return self._fallback(champion_id, alive_opponent_ids, errors)

        return ParseResult(
            success=len(errors) == 0,
            actions=parsed_actions,
            errors=errors,
            used_fallback=False,
        )

    def _fallback(
        self,
        champion_id: str,
        alive_opponent_ids: list[str],
        errors: list[str],
    ) -> ParseResult:
        """
        Generate a fallback action when the bot's response is invalid.

        Uses basic_strike on a random alive opponent. If no opponents are
        alive, returns an empty action list (the match is over anyway).

        Args:
            champion_id: The bot's champion ID.
            alive_opponent_ids: IDs of living opponents.
            errors: Accumulated error messages.

        Returns:
            ParseResult with a single basic_strike fallback action.
        """
        errors.append("Using fallback action: basic_strike")

        if not alive_opponent_ids:
            return ParseResult(
                success=False,
                actions=[],
                errors=errors,
                used_fallback=True,
            )

        target = random.choice(alive_opponent_ids)
        return ParseResult(
            success=False,
            actions=[
                ParsedAction(
                    action_name="basic_strike",
                    target_id=target,
                    action_point_cost=1,
                )
            ],
            errors=errors,
            used_fallback=True,
        )

    def actions_to_engine_format(self, parsed_actions: list[ParsedAction]) -> list[dict]:
        """
        Convert ParsedActions to the format the battle engine expects.

        The battle engine uses dicts with 'name' and 'target_id' keys.

        Args:
            parsed_actions: List of validated ParsedAction objects.

        Returns:
            List of action dicts ready for the battle engine.
        """
        return [
            {"name": pa.action_name, "target_id": pa.target_id}
            for pa in parsed_actions
        ]
