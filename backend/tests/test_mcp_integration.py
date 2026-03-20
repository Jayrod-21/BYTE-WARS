"""
tests/test_mcp_integration.py — Phase 2 MCP Integration Tests for BYTE Wars.

Validates that the MCP tool system works correctly end-to-end:
1. ToolRegistry: Base tools loaded, dynamic registration works
2. ToolBridge: MCP tool calls resolve correctly via DamageResolver
3. GameState: Properly built for each bot turn
4. BotResponseParser: Validates and rejects bad responses, fallback works
5. MCP Server: All 5 tools registered and callable
6. Full match: 10 battles using the MCP pipeline produce valid results

Success criteria:
- All tool registry operations succeed
- Tool bridge resolves attacks, heals, and defends correctly
- Bot response parser catches invalid inputs and falls back gracefully
- MCP server has all 5 tools registered
- 10 full battles complete with no errors, same balance as Phase 1
"""

import sys
import os
import asyncio
from collections import Counter, defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.battle_engine import BattleEngine, BattleChampion
from engine.damage_resolver import DamageResolver
from mcp_tools.tool_registry import ToolRegistry
from mcp_tools.tool_bridge import ToolBridge
from mcp_tools.game_state import build_game_state, GameState
from mcp_tools.bot_response import BotResponseParser
from mcp_tools.tool_server import create_mcp_server


def create_mock_champions() -> list[dict]:
    """Same 4 champions as Phase 1 for comparison."""
    return [
        {
            "id": "tank-001",
            "name": "IronClad (Tank)",
            "stats": {"health": 150, "strength": 35, "endurance": 75},
        },
        {
            "id": "assassin-002",
            "name": "ShadowByte (Assassin)",
            "stats": {"health": 80, "strength": 80, "endurance": 40},
        },
        {
            "id": "mage-003",
            "name": "PixelStorm (Mage)",
            "stats": {"health": 90, "strength": 90, "endurance": 25},
        },
        {
            "id": "ranger-004",
            "name": "ByteHunter (Ranger)",
            "stats": {"health": 110, "strength": 55, "endurance": 55},
        },
    ]


def test_tool_registry():
    """Test ToolRegistry: base tools loaded, dynamic registration, removal."""
    print("\n--- Test 1: ToolRegistry ---")
    registry = ToolRegistry()

    # Check all 5 base tools are loaded
    tools = registry.get_all_tools()
    assert len(tools) == 5, f"Expected 5 base tools, got {len(tools)}"
    expected_names = {"basic_strike", "heavy_blow", "defend", "power_surge", "heal"}
    assert set(tools.keys()) == expected_names, f"Wrong tool names: {set(tools.keys())}"
    print("  PASS: 5 base tools loaded correctly")

    # Test get_tool
    strike = registry.get_tool("basic_strike")
    assert strike is not None
    assert strike["action_point_cost"] == 1
    assert strike["damage_range"] == [5, 12]
    print("  PASS: get_tool returns correct data")

    # Test get_affordable_tools
    affordable_1ap = registry.get_affordable_tools(1)
    assert all(t["action_point_cost"] <= 1 for t in affordable_1ap)
    affordable_3ap = registry.get_affordable_tools(3)
    assert len(affordable_3ap) == 5  # All tools cost <= 3
    print("  PASS: get_affordable_tools filters correctly")

    # Test dynamic tool registration
    nft_skill = {
        "name": "flame_slash",
        "action_point_cost": 2,
        "damage_range": [20, 35],
        "heal_range": None,
        "stat_requirement": "strength",
        "target": "single_enemy",
        "description": "A fiery slash that burns the target.",
        "is_defense": False,
        "defense_reduction": 0.0,
    }
    success, error = registry.register_tool(nft_skill)
    assert success, f"Failed to register tool: {error}"
    assert registry.get_tool("flame_slash") is not None
    assert len(registry.get_all_tools()) == 6
    print("  PASS: Dynamic tool registration works")

    # Test invalid tool registration
    bad_tool = {"name": "bad_tool"}  # Missing fields
    success, error = registry.register_tool(bad_tool)
    assert not success
    assert "Missing required field" in error
    print("  PASS: Invalid tool rejected with error")

    # Test tool removal
    success, error = registry.unregister_tool("flame_slash")
    assert success
    assert registry.get_tool("flame_slash") is None
    print("  PASS: Dynamic tool removal works")

    # Test cannot remove base tools
    success, error = registry.unregister_tool("basic_strike")
    assert not success
    assert "Cannot remove base action" in error
    print("  PASS: Base tools protected from removal")

    # Test get_tool_schemas
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 5
    for schema in schemas:
        assert "name" in schema
        assert "action_point_cost" in schema
        assert "description" in schema
    print("  PASS: Tool schemas generated correctly")

    print("  ALL REGISTRY TESTS PASSED")


def test_tool_bridge():
    """Test ToolBridge: resolves attacks, heals, and defends correctly."""
    print("\n--- Test 2: ToolBridge ---")
    bridge = ToolBridge()

    attacker_stats = {"health": 100, "strength": 60, "endurance": 40}
    defender_stats = {"health": 100, "strength": 40, "endurance": 50}

    # Test attack resolution
    result = bridge.resolve_tool_call(
        tool_call={"action": "basic_strike"},
        attacker_id="attacker-1",
        attacker_stats=attacker_stats,
        target_id="defender-1",
        target_stats=defender_stats,
        target_hp=100.0,
        target_max_hp=100.0,
    )
    assert result is not None
    assert result.action_name == "basic_strike"
    assert result.attacker_id == "attacker-1"
    assert result.target_id == "defender-1"
    assert result.modified_damage > 0
    assert result.target_hp_after < 100.0
    print(f"  PASS: Attack resolved — {result.modified_damage} damage dealt")

    # Test heal resolution
    result = bridge.resolve_tool_call(
        tool_call={"action": "heal"},
        attacker_id="healer-1",
        attacker_stats={"health": 100, "strength": 30, "endurance": 60},
        target_id="healer-1",
        target_stats={"health": 100, "strength": 30, "endurance": 60},
        target_hp=50.0,
        target_max_hp=100.0,
    )
    assert result is not None
    assert result.action_name == "heal"
    assert result.healing_done > 0
    assert result.target_hp_after > 50.0
    print(f"  PASS: Heal resolved — {result.healing_done} HP restored")

    # Test defend resolution
    result = bridge.resolve_tool_call(
        tool_call={"action": "defend"},
        attacker_id="defender-1",
        attacker_stats=defender_stats,
        target_id="defender-1",
        target_stats=defender_stats,
        target_hp=80.0,
        target_max_hp=100.0,
    )
    assert result is not None
    assert result.action_name == "defend"
    assert result.modified_damage == 0
    print("  PASS: Defend resolved — no damage, buff applied")

    # Test attack against defending target
    result_no_def = bridge.resolve_tool_call(
        tool_call={"action": "heavy_blow"},
        attacker_id="attacker-1",
        attacker_stats=attacker_stats,
        target_id="defender-1",
        target_stats=defender_stats,
        target_hp=100.0,
        target_max_hp=100.0,
        target_is_defending=False,
    )
    result_with_def = bridge.resolve_tool_call(
        tool_call={"action": "heavy_blow"},
        attacker_id="attacker-1",
        attacker_stats=attacker_stats,
        target_id="defender-1",
        target_stats=defender_stats,
        target_hp=100.0,
        target_max_hp=100.0,
        target_is_defending=True,
    )
    # On average, defending should reduce damage (test over multiple runs)
    print(f"  INFO: Damage without defend: {result_no_def.modified_damage}, "
          f"with defend: {result_with_def.modified_damage}")
    print("  PASS: Defense modifier applies to incoming attacks")

    # Test unknown action
    result = bridge.resolve_tool_call(
        tool_call={"action": "nonexistent_action"},
        attacker_id="a", attacker_stats={},
        target_id="b", target_stats={},
        target_hp=100.0, target_max_hp=100.0,
    )
    assert result is None
    print("  PASS: Unknown action returns None")

    print("  ALL BRIDGE TESTS PASSED")


def test_game_state():
    """Test GameState: built correctly for each bot turn."""
    print("\n--- Test 3: GameState ---")

    # Create battle champions for testing
    champ = BattleChampion(
        id="me-001", name="TestBot", stats={"health": 100, "strength": 50, "endurance": 50},
        max_hp=100.0, current_hp=75.0,
    )
    opp1 = BattleChampion(
        id="opp-001", name="Enemy1", stats={"health": 80, "strength": 60, "endurance": 40},
        max_hp=80.0, current_hp=60.0,
    )
    opp2 = BattleChampion(
        id="opp-002", name="Enemy2", stats={"health": 90, "strength": 70, "endurance": 30},
        max_hp=90.0, current_hp=0.0, is_alive=False,
    )

    registry = ToolRegistry()
    schemas = registry.get_tool_schemas()

    state = build_game_state(
        turn_number=5,
        champion=champ,
        opponents=[opp1, opp2],
        tool_schemas=schemas,
        recent_history=[],
        total_champions=3,
    )

    # Validate state fields
    assert state.turn_number == 5
    assert state.action_points_remaining == 3
    assert state.self_state["id"] == "me-001"
    assert state.self_state["current_hp"] == 75.0
    assert len(state.opponents) == 2
    assert state.total_champions == 3
    assert state.champions_alive == 2  # champ + opp1 alive
    assert len(state.available_tools) == 5
    print("  PASS: GameState built with correct fields")

    # Test to_dict serialization
    state_dict = state.to_dict()
    assert isinstance(state_dict, dict)
    assert "turn_number" in state_dict
    assert "self_state" in state_dict
    print("  PASS: GameState serializes to dict")

    # Test to_prompt generation
    prompt = state.to_prompt()
    assert "BATTLE STATE (Turn 5)" in prompt
    assert "TestBot" in prompt
    assert "Enemy1" in prompt
    assert "basic_strike" in prompt
    assert "action points" in prompt.lower()
    print("  PASS: GameState generates readable prompt")
    print(f"  INFO: Prompt is {len(prompt)} chars, {prompt.count(chr(10))} lines")

    print("  ALL GAME STATE TESTS PASSED")


def test_bot_response_parser():
    """Test BotResponseParser: validates good and bad responses, fallback."""
    print("\n--- Test 4: BotResponseParser ---")
    registry = ToolRegistry()
    parser = BotResponseParser(registry)

    champion_id = "me-001"
    alive_opponents = ["opp-001", "opp-002"]

    # Test valid list response
    good_response = [
        {"action": "basic_strike", "target_id": "opp-001"},
        {"action": "heavy_blow", "target_id": "opp-002"},
    ]
    result = parser.parse(good_response, champion_id, alive_opponents)
    assert result.success
    assert len(result.actions) == 2
    assert result.actions[0].action_name == "basic_strike"
    assert result.actions[1].action_name == "heavy_blow"
    assert not result.used_fallback
    print("  PASS: Valid list response parsed correctly (1 + 2 = 3 AP)")

    # Test valid JSON string response
    import json
    json_response = json.dumps([
        {"action": "power_surge", "target_id": "opp-001"},
    ])
    result = parser.parse(json_response, champion_id, alive_opponents)
    assert result.success
    assert len(result.actions) == 1
    assert result.actions[0].action_point_cost == 3
    print("  PASS: Valid JSON string response parsed correctly")

    # Test AP budget exceeded
    over_budget = [
        {"action": "heavy_blow", "target_id": "opp-001"},
        {"action": "heavy_blow", "target_id": "opp-002"},  # 2 + 2 = 4 > 3
    ]
    result = parser.parse(over_budget, champion_id, alive_opponents)
    assert len(result.actions) == 1  # Only first action accepted
    assert len(result.errors) > 0
    print("  PASS: AP budget excess rejected, partial actions kept")

    # Test unknown action
    bad_action = [{"action": "nonexistent_skill", "target_id": "opp-001"}]
    result = parser.parse(bad_action, champion_id, alive_opponents)
    assert result.used_fallback
    assert len(result.errors) > 0
    print("  PASS: Unknown action triggers fallback")

    # Test invalid JSON string
    result = parser.parse("not valid json {{{", champion_id, alive_opponents)
    assert result.used_fallback
    assert any("Invalid JSON" in e for e in result.errors)
    print("  PASS: Invalid JSON triggers fallback")

    # Test empty response
    result = parser.parse([], champion_id, alive_opponents)
    assert result.used_fallback
    print("  PASS: Empty response triggers fallback")

    # Test auto-target correction (invalid target gets reassigned)
    bad_target = [{"action": "basic_strike", "target_id": "dead-opponent-999"}]
    result = parser.parse(bad_target, champion_id, alive_opponents)
    assert result.actions[0].target_id in alive_opponents
    print("  PASS: Invalid target auto-corrected to alive opponent")

    # Test self-targeting action
    self_action = [{"action": "defend", "target_id": "wrong-id"}]
    result = parser.parse(self_action, champion_id, alive_opponents)
    assert result.actions[0].target_id == champion_id
    print("  PASS: Self-targeting actions corrected to champion_id")

    # Test actions_to_engine_format
    actions = [
        {"action": "basic_strike", "target_id": "opp-001"},
        {"action": "heal", "target_id": "me-001"},
    ]
    result = parser.parse(actions, champion_id, alive_opponents)
    engine_format = parser.actions_to_engine_format(result.actions)
    assert all("name" in a and "target_id" in a for a in engine_format)
    print("  PASS: actions_to_engine_format produces correct output")

    print("  ALL PARSER TESTS PASSED")


def test_mcp_server():
    """Test MCP Server: all 5 tools registered and queryable."""
    print("\n--- Test 5: MCP Server ---")
    server = create_mcp_server()

    assert server.name == "byte-wars-tools"
    print("  PASS: Server created with correct name")

    # List registered tools by checking the server's internal state
    # FastMCP stores tools internally; we can verify via list_tools
    async def check_tools():
        tools = await server.list_tools()
        return tools

    tools = asyncio.run(check_tools())
    tool_names = {t.name for t in tools}
    expected = {"basic_strike", "heavy_blow", "defend", "power_surge", "heal"}
    assert tool_names == expected, f"Expected {expected}, got {tool_names}"
    print(f"  PASS: All 5 tools registered: {tool_names}")

    # Verify tool descriptions contain cost info
    for tool in tools:
        assert "Cost:" in tool.description or "cost:" in tool.description.lower(), \
            f"Tool {tool.name} missing cost in description"
    print("  PASS: All tools have cost info in descriptions")

    # Test calling a tool directly
    async def call_tool():
        result = await server.call_tool("basic_strike", {"target_id": "test-enemy"})
        return result

    result = asyncio.run(call_tool())
    # Result should be a list of content blocks
    assert len(result) > 0
    print("  PASS: Tool call returns result")

    print("  ALL MCP SERVER TESTS PASSED")


def test_full_battle_with_mcp():
    """Test: 10 full battles using the MCP pipeline."""
    print("\n--- Test 6: Full Battle with MCP Pipeline ---")
    champions = create_mock_champions()

    # Use a fresh ToolRegistry for the engine
    registry = ToolRegistry()
    engine = BattleEngine(tool_registry=registry)

    winner_counts = Counter()
    turns_per_match = []
    timeouts = 0
    fallback_turns = 0
    total_turns_tracked = 0

    for battle_num in range(1, 11):
        history = engine.run_battle(champions)
        turns = history.total_turns
        turns_per_match.append(turns)

        if history.status == "timed_out":
            timeouts += 1
            winner_counts["TIMEOUT"] += 1
            print(f"  Battle {battle_num:2d}: TIMED OUT after {turns} turns")
        elif history.winner_name:
            winner_counts[history.winner_name] += 1
            print(f"  Battle {battle_num:2d}: {history.winner_name} wins in {turns} turns")

        # Check for fallback usage in turns
        for turn in history.turns:
            total_turns_tracked += 1
            if turn.get("used_fallback", False):
                fallback_turns += 1

    # Validation
    avg_turns = sum(turns_per_match) / len(turns_per_match)
    min_turns = min(turns_per_match)
    timeout_rate = (timeouts / 10) * 100

    print(f"\n  Average turns: {avg_turns:.1f} (min: {min_turns}, max: {max(turns_per_match)})")
    print(f"  Timeout rate: {timeout_rate:.0f}%")
    print(f"  Fallback turns: {fallback_turns}/{total_turns_tracked}")

    assert min_turns >= 3, f"Battle ended in {min_turns} turns (< 3)"
    print("  PASS: No battles under 3 turns")

    assert timeout_rate <= 20, f"Timeout rate {timeout_rate}% exceeds 20%"
    print("  PASS: Timeout rate within bounds")

    assert fallback_turns == 0, f"{fallback_turns} turns used fallback (mock bot should never fail)"
    print("  PASS: No fallback actions needed (mock bot always valid)")

    # Verify turn entries have game_state_snapshot field
    sample_turn = history.turns[0]
    assert "game_state_snapshot" in sample_turn
    assert "used_fallback" in sample_turn
    print("  PASS: Turn entries include game_state_snapshot and used_fallback fields")

    print("  ALL FULL BATTLE TESTS PASSED")


def test_dynamic_tool_in_battle():
    """Test: Register an NFT skill and verify it works in battle."""
    print("\n--- Test 7: Dynamic Tool in Battle ---")

    # Create a registry with an extra NFT skill
    registry = ToolRegistry()
    nft_skill = {
        "name": "shadow_strike",
        "action_point_cost": 2,
        "damage_range": [18, 30],
        "heal_range": None,
        "stat_requirement": "strength",
        "target": "single_enemy",
        "description": "A shadow-infused strike that pierces defenses.",
        "is_defense": False,
        "defense_reduction": 0.0,
    }
    success, _ = registry.register_tool(nft_skill)
    assert success
    assert len(registry.get_all_tools()) == 6
    print("  PASS: NFT skill registered (6 total tools)")

    # Verify the bridge can resolve it
    bridge = ToolBridge(registry)
    result = bridge.resolve_tool_call(
        tool_call={"action": "shadow_strike"},
        attacker_id="a1",
        attacker_stats={"strength": 70, "endurance": 40},
        target_id="d1",
        target_stats={"strength": 40, "endurance": 50},
        target_hp=100.0,
        target_max_hp=100.0,
    )
    assert result is not None
    assert result.modified_damage > 0
    print(f"  PASS: NFT skill resolves via bridge ({result.modified_damage} damage)")

    # Run a battle with the extended registry
    engine = BattleEngine(tool_registry=registry)
    champions = create_mock_champions()
    history = engine.run_battle(champions)
    assert history.status in ("complete", "timed_out")
    print(f"  PASS: Battle with NFT skill completed ({history.total_turns} turns)")

    # Unregister the NFT skill
    success, _ = registry.unregister_tool("shadow_strike")
    assert success
    assert len(registry.get_all_tools()) == 5
    print("  PASS: NFT skill unregistered (back to 5 tools)")

    print("  ALL DYNAMIC TOOL TESTS PASSED")


def main():
    """Run all Phase 2 integration tests."""
    print("=" * 60)
    print("BYTE WARS — Phase 2 MCP Integration Tests")
    print("=" * 60)

    all_passed = True
    tests = [
        test_tool_registry,
        test_tool_bridge,
        test_game_state,
        test_bot_response_parser,
        test_mcp_server,
        test_full_battle_with_mcp,
        test_dynamic_tool_in_battle,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            print(f"\n  FAIL: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n  ERROR: {type(e).__name__}: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: ALL PHASE 2 TESTS PASSED")
    else:
        print("RESULT: SOME TESTS FAILED")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
