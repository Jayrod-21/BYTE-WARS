"""
tests/test_battle.py — Battle Engine validation script for BYTE Wars Phase 1.

Creates 4 mock champions with different stat distributions (one per archetype),
runs 10 complete battles, and prints a summary report including:
- Winner distribution (which champion/archetype wins most)
- Average turns per match
- Most used actions
- Average damage per action type
- Timeout rate (must be < 20%)
- Minimum turns check (no battle < 3 turns)

Success criteria:
- All 10 battles complete without errors
- No battle ends in under 3 turns
- Timeout rate < 20%
"""

import sys
import os
from collections import Counter, defaultdict

# Add parent directory to path so we can import engine modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.battle_engine import BattleEngine


def create_mock_champions() -> list[dict]:
    """
    Create 4 mock champions with different stat distributions.

    Each champion represents a different archetype with distinct strengths:
    - Tank: High health, high endurance, low strength
    - Assassin: Low health, high strength, low endurance
    - Mage: Medium health, very high strength, very low endurance
    - Ranger: Balanced stats across the board
    """
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


def run_test_battles(num_battles: int = 10):
    """
    Run multiple battles and collect statistics for balance validation.

    Args:
        num_battles: Number of complete battles to simulate.
    """
    engine = BattleEngine()
    champions = create_mock_champions()

    # --- Statistics tracking ---
    winner_counts = Counter()         # How many times each champion won
    turns_per_match = []              # Turn count for each match
    action_usage = Counter()          # How many times each action was used
    action_damage = defaultdict(list) # Damage values per action type
    timeouts = 0                      # Matches that hit the turn limit
    short_battles = 0                 # Battles under 3 turns (should be 0)

    print("=" * 60)
    print("BYTE WARS — Phase 1 Battle Engine Test")
    print(f"Running {num_battles} battles with 4 champions each")
    print("=" * 60)
    print()

    for battle_num in range(1, num_battles + 1):
        # Run the battle
        history = engine.run_battle(champions)

        # Track results
        turns = history.total_turns
        turns_per_match.append(turns)

        if history.status == "timed_out":
            timeouts += 1
            winner_counts["TIMEOUT (no winner)"] += 1
            print(f"  Battle {battle_num:2d}: TIMED OUT after {turns} turns")
        elif history.winner_name:
            winner_counts[history.winner_name] += 1
            print(f"  Battle {battle_num:2d}: {history.winner_name} wins in {turns} turns")
        else:
            winner_counts["DRAW (all eliminated)"] += 1
            print(f"  Battle {battle_num:2d}: DRAW in {turns} turns")

        if turns < 3:
            short_battles += 1
            print(f"    WARNING: Battle ended in {turns} turns (< 3 minimum)")

        # Collect action statistics from turn history
        for turn in history.turns:
            for action_taken in turn.get("actions_taken", []):
                action_name = action_taken["action"]
                action_usage[action_name] += 1

            for resolution in turn.get("resolutions", []):
                action_name = resolution["action"]
                if resolution["modified_damage"] > 0:
                    action_damage[action_name].append(resolution["modified_damage"])

    # --- Print Summary Report ---
    print()
    print("=" * 60)
    print("BATTLE SUMMARY REPORT")
    print("=" * 60)

    # Winner distribution
    print("\n--- Winner Distribution ---")
    for name, count in winner_counts.most_common():
        pct = (count / num_battles) * 100
        bar = "#" * int(pct / 2)
        print(f"  {name:30s}: {count:2d} wins ({pct:5.1f}%) {bar}")

    # Average turns per match
    avg_turns = sum(turns_per_match) / len(turns_per_match)
    min_turns = min(turns_per_match)
    max_turns = max(turns_per_match)
    print(f"\n--- Match Duration ---")
    print(f"  Average turns: {avg_turns:.1f}")
    print(f"  Min turns:     {min_turns}")
    print(f"  Max turns:     {max_turns}")

    # Most used actions
    print(f"\n--- Action Usage ---")
    total_actions = sum(action_usage.values())
    for action_name, count in action_usage.most_common():
        pct = (count / total_actions) * 100
        print(f"  {action_name:15s}: {count:4d} uses ({pct:5.1f}%)")

    # Average damage per action type
    print(f"\n--- Average Damage per Action ---")
    for action_name, damages in sorted(action_damage.items()):
        if damages:
            avg_dmg = sum(damages) / len(damages)
            print(f"  {action_name:15s}: {avg_dmg:6.1f} avg damage ({len(damages)} hits)")

    # --- Validation Checks ---
    print()
    print("=" * 60)
    print("VALIDATION CHECKS")
    print("=" * 60)

    timeout_rate = (timeouts / num_battles) * 100
    checks_passed = True

    # Check 1: No battle < 3 turns
    if short_battles > 0:
        print(f"  FAIL: {short_battles} battle(s) ended in < 3 turns")
        checks_passed = False
    else:
        print(f"  PASS: No battles ended in < 3 turns (min: {min_turns})")

    # Check 2: Timeout rate < 20%
    if timeout_rate > 20:
        print(f"  FAIL: Timeout rate {timeout_rate:.1f}% exceeds 20% threshold")
        checks_passed = False
    else:
        print(f"  PASS: Timeout rate {timeout_rate:.1f}% (< 20% threshold)")

    # Check 3: All battles completed without errors
    print(f"  PASS: All {num_battles} battles completed without errors")

    # Overall result
    print()
    if checks_passed:
        print("RESULT: ALL CHECKS PASSED — Engine is ready for Phase 2")
    else:
        print("RESULT: SOME CHECKS FAILED — Stats need rebalancing")

    print("=" * 60)

    return checks_passed


if __name__ == "__main__":
    success = run_test_battles(10)
    sys.exit(0 if success else 1)
