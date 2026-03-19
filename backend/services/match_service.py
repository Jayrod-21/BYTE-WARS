"""
services/match_service.py — Match orchestration service for BYTE Wars.

Handles the complete match lifecycle:
1. Match creation with lobby (2-4 champions)
2. State machine: pending → active → complete | timed_out
3. Async match execution (non-blocking — runs in background)
4. AI bot integration (real API calls per champion)
5. Bot response timeout handling (fallback to random if AI is slow)
6. Winner determination and result storage
7. Match history retrieval

The match service bridges the champion system (Phase 3) with the
battle engine (Phase 1-2), using real AI bots (Phase 4) instead of MockBot.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from dataclasses import asdict

from engine.battle_engine import BattleEngine, BattleChampion, BattleHistory, MockBot, TURN_LIMIT
from engine.ai_bot import AIBot
from mcp_tools.tool_registry import ToolRegistry
from mcp_tools.tool_bridge import ToolBridge
from mcp_tools.game_state import build_game_state
from mcp_tools.bot_response import BotResponseParser
from engine.turn_manager import TurnManager
from services.champion_service import decrypt_api_key


# Match states
MATCH_PENDING = "pending"
MATCH_ACTIVE = "active"
MATCH_COMPLETE = "complete"
MATCH_TIMED_OUT = "timed_out"

# In-memory match store (replaced with DB in later phases)
_matches_store: dict[str, dict] = {}

# Track running match tasks so we can check status
_running_tasks: dict[str, asyncio.Task] = {}


class MatchService:
    """
    Orchestrates match creation, execution, and result storage.

    Flow:
    1. create_match() — validates champions, creates a pending match
    2. start_match() — transitions to active, runs battle asynchronously
    3. Battle engine runs with AI bots (or MockBot fallback)
    4. On completion — stores results, transitions to complete/timed_out
    """

    def __init__(self):
        self.registry = ToolRegistry()

    def create_match(
        self,
        champion_data_list: list[dict],
    ) -> dict:
        """
        Create a new match with 2-4 champions in the lobby.

        Args:
            champion_data_list: List of champion data dicts (from champion store).

        Returns:
            Match data dict with status "pending".

        Raises:
            ValueError: If champion count is invalid.
        """
        if len(champion_data_list) < 2:
            raise ValueError("A match requires at least 2 champions.")
        if len(champion_data_list) > 4:
            raise ValueError("A match supports at most 4 champions.")

        match_id = str(uuid.uuid4())
        champion_ids = [str(c["id"]) for c in champion_data_list]
        champion_names = [c["name"] for c in champion_data_list]

        match_data = {
            "id": match_id,
            "status": MATCH_PENDING,
            "champion_ids": champion_ids,
            "champion_names": champion_names,
            "champion_data": champion_data_list,  # Full data for battle execution
            "winner_id": None,
            "winner_name": None,
            "turn_history": [],
            "total_turns": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "resolved_at": None,
        }

        _matches_store[match_id] = match_data
        return match_data

    async def start_match(self, match_id: str) -> dict:
        """
        Start executing a pending match asynchronously.

        Transitions match from pending → active and kicks off the battle
        in a background task.

        Args:
            match_id: The match to start.

        Returns:
            Updated match data with status "active".

        Raises:
            ValueError: If match doesn't exist or isn't pending.
        """
        match_data = _matches_store.get(match_id)
        if match_data is None:
            raise ValueError(f"Match '{match_id}' not found.")
        if match_data["status"] != MATCH_PENDING:
            raise ValueError(
                f"Match '{match_id}' is '{match_data['status']}', not pending."
            )

        # Transition to active
        match_data["status"] = MATCH_ACTIVE
        match_data["started_at"] = datetime.now(timezone.utc).isoformat()

        # Execute battle (async but awaited — non-blocking for other requests)
        await self._execute_battle(match_id)

        return _matches_store[match_id]

    async def _execute_battle(self, match_id: str):
        """
        Run the full battle and store results.

        Creates AI bots for champions with API keys, MockBot for others.
        Runs the battle engine and updates the match data on completion.
        """
        match_data = _matches_store.get(match_id)
        if match_data is None:
            return

        champion_data_list = match_data["champion_data"]

        try:
            # Build bots for each champion
            bots = {}
            for champ in champion_data_list:
                champ_id = str(champ["id"])
                api_key = champ.get("api_key")
                model = champ.get("model", "claude-sonnet-4-6")
                system_prompt = champ.get("system_prompt", "")

                if api_key:
                    # Decrypt the API key and create a real AI bot
                    try:
                        decrypted_key = decrypt_api_key(api_key)
                        bots[champ_id] = AIBot(
                            api_key=decrypted_key,
                            model=model,
                            system_prompt=system_prompt,
                        )
                    except ValueError:
                        # Decryption failed — fall back to MockBot
                        bots[champ_id] = MockBot()
                else:
                    bots[champ_id] = MockBot()

            # Run the battle with per-champion bots
            history = await self._run_battle_with_bots(
                champion_data_list, bots
            )

            # Store results
            match_data["status"] = history.status
            match_data["winner_id"] = history.winner_id
            match_data["winner_name"] = history.winner_name
            match_data["turn_history"] = history.turns
            match_data["total_turns"] = history.total_turns
            match_data["resolved_at"] = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            # If battle crashes, mark as timed_out with error info
            match_data["status"] = MATCH_TIMED_OUT
            match_data["resolved_at"] = datetime.now(timezone.utc).isoformat()
            match_data["error"] = str(e)

        # Clean up task reference
        _running_tasks.pop(match_id, None)

    async def _run_battle_with_bots(
        self,
        champions_data: list[dict],
        bots: dict,  # champ_id -> bot instance
    ) -> BattleHistory:
        """
        Run the battle engine with per-champion bot selection.

        This replaces the engine's built-in MockBot with champion-specific
        bots (AIBot for champions with API keys, MockBot for others).

        Uses the same resolution pipeline as the standard engine:
        ToolRegistry → BotResponseParser → ToolBridge → DamageResolver
        """
        if len(champions_data) < 2 or len(champions_data) > 4:
            raise ValueError(
                f"Battle requires 2-4 champions, got {len(champions_data)}"
            )

        registry = self.registry
        bridge = ToolBridge(registry)
        turn_manager = TurnManager()
        parser = BotResponseParser(registry)
        mock_bot = MockBot()

        match_id = str(uuid.uuid4())
        fighters = [BattleChampion.from_dict(c) for c in champions_data]
        all_tools = registry.get_all_tools()
        tool_schemas = registry.get_tool_schemas()

        history = BattleHistory(
            match_id=match_id,
            champion_ids=[f.id for f in fighters],
            champion_names=[f.name for f in fighters],
            status="active",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        initiative_order = turn_manager.roll_initiative(champions_data)
        ordered_ids = [str(cid) for cid in initiative_order.get_ordered_ids()]

        for turn_number in range(1, TURN_LIMIT + 1):
            history.total_turns = turn_number

            for fighter in fighters:
                fighter.is_defending = False

            for champion_id in ordered_ids:
                champion = next(
                    (f for f in fighters if f.id == champion_id), None
                )
                if champion is None or not champion.is_alive:
                    continue

                opponents = [
                    f for f in fighters if f.is_alive and f.id != champion_id
                ]
                if not opponents:
                    break

                # Build game state
                game_state = build_game_state(
                    turn_number=turn_number,
                    champion=champion,
                    opponents=[f for f in fighters if f.id != champion_id],
                    tool_schemas=tool_schemas,
                    recent_history=history.turns[-6:],
                    total_champions=len(fighters),
                )

                # Select bot for this champion
                bot = bots.get(champion_id, mock_bot)

                # Get actions — use async for AIBot, sync for MockBot
                if isinstance(bot, AIBot):
                    try:
                        raw_response = await asyncio.wait_for(
                            bot.choose_actions_async(
                                champion, opponents, all_tools, game_state
                            ),
                            timeout=12.0,
                        )
                    except asyncio.TimeoutError:
                        raw_response = bot._random_fallback(
                            champion, opponents, all_tools
                        )
                else:
                    raw_response = bot.choose_actions(
                        champion, opponents, all_tools, game_state
                    )

                # Parse and validate
                alive_opponent_ids = [o.id for o in opponents if o.is_alive]
                parse_result = parser.parse(
                    raw_response, champion_id, alive_opponent_ids
                )
                chosen_actions = parser.actions_to_engine_format(
                    parse_result.actions
                )

                # Resolve actions (same as BattleEngine)
                from engine.battle_engine import TurnEntry
                turn_entry = TurnEntry(
                    turn_number=turn_number,
                    champion_id=champion_id,
                    champion_name=champion.name,
                    used_fallback=parse_result.used_fallback,
                )

                for action_choice in chosen_actions:
                    action_name = action_choice["name"]
                    action_def = registry.get_tool(action_name)
                    if action_def is None:
                        continue

                    target_id = action_choice.get("target_id", champion_id)

                    turn_entry.actions_taken.append({
                        "action": action_name,
                        "target_id": target_id,
                        "cost": action_def["action_point_cost"],
                    })

                    result = None

                    if action_def["is_defense"]:
                        champion.is_defending = True
                        result = bridge.resolve_tool_call(
                            {"action": action_name},
                            attacker_id=champion_id,
                            attacker_stats=champion.stats,
                            target_id=champion_id,
                            target_stats=champion.stats,
                            target_hp=champion.current_hp,
                            target_max_hp=champion.max_hp,
                        )

                    elif action_def["heal_range"] is not None:
                        result = bridge.resolve_tool_call(
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
                        target = next(
                            (f for f in fighters if f.id == target_id), None
                        )
                        if target is None or not target.is_alive:
                            continue

                        result = bridge.resolve_tool_call(
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

                history.turns.append(asdict(turn_entry))

            # Check win condition
            alive = [f for f in fighters if f.is_alive]

            if len(alive) == 1:
                history.winner_id = alive[0].id
                history.winner_name = alive[0].name
                history.status = "complete"
                history.ended_at = datetime.now(timezone.utc).isoformat()
                return history

            if len(alive) == 0:
                history.status = "complete"
                history.ended_at = datetime.now(timezone.utc).isoformat()
                return history

        # Turn limit exceeded
        history.status = "timed_out"
        history.ended_at = datetime.now(timezone.utc).isoformat()
        return history

    def get_match(self, match_id: str) -> dict | None:
        """Retrieve a match by ID."""
        return _matches_store.get(match_id)

    def list_matches(self, status: str | None = None) -> list[dict]:
        """List all matches, optionally filtered by status."""
        matches = _matches_store.values()
        if status:
            matches = [m for m in matches if m.get("status") == status]
        return list(matches)

    def to_response(self, match_data: dict) -> dict:
        """
        Convert match data to API response format.

        Strips internal champion_data (contains encrypted API keys)
        and returns only safe, public information.
        """
        return {
            "id": match_data["id"],
            "status": match_data["status"],
            "champion_ids": match_data["champion_ids"],
            "champion_names": match_data.get("champion_names", []),
            "winner_id": match_data.get("winner_id"),
            "winner_name": match_data.get("winner_name"),
            "total_turns": match_data.get("total_turns", 0),
            "turn_history": match_data.get("turn_history", []),
            "created_at": match_data.get("created_at"),
            "started_at": match_data.get("started_at"),
            "resolved_at": match_data.get("resolved_at"),
        }


def clear_store():
    """Clear match store. Used by tests."""
    _matches_store.clear()
    _running_tasks.clear()
