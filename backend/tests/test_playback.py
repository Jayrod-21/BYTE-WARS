"""
tests/test_playback.py — Phase 5 Playback & Visualization Tests.

Tests the full playback pipeline:
1. Run a match to completion
2. Convert battle history to playback events
3. Verify all event types are present
4. Verify event ordering and timing
5. Verify sprite generation for all archetypes
6. Verify HTML playback viewer renders
7. Verify shareable link generation
8. Verify match summary stats
9. Test error cases (pending match, non-existent match)
10. Full end-to-end: create → fight → playback
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from httpx import ASGITransport

from main import app
from tests._auth import login_default_user
from routes.champion import clear_store as clear_champions
from services.match_service import clear_store as clear_matches


async def run_tests():
    """Run all Phase 5 tests."""
    clear_champions()
    clear_matches()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        await login_default_user(client)


        # --- Setup: Create champions and run a match ---
        print("\n--- Setup: Create Champions & Run Match ---")
        champion_ids = []
        for arch in ["tank", "assassin", "mage", "ranger"]:
            resp = await client.post("/api/champions", json={
                "name": f"Playback {arch.title()}",
                "archetype": arch,
            })
            assert resp.status_code == 201
            champion_ids.append(resp.json()["id"])

        # Create and start a 1v1 match
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids[:2],
        })
        assert resp.status_code == 201
        match_id = resp.json()["id"]

        resp = await client.post(f"/api/matches/{match_id}/start")
        assert resp.status_code == 200
        match_result = resp.json()
        assert match_result["status"] in ("complete", "timed_out")
        print(f"  Match complete: {match_result['status']} in {match_result['total_turns']} turns")

        # ========================================
        # Test 1: GET /playback/{id} — Playback Data
        # ========================================
        print("\n--- Test 1: Playback Data Endpoint ---")
        resp = await client.get(f"/api/playback/{match_id}")
        assert resp.status_code == 200
        playback = resp.json()
        assert playback["match_id"] == match_id
        assert len(playback["events"]) > 0
        assert len(playback["champions"]) == 2
        assert playback["status"] in ("complete", "timed_out")
        print(f"  PASS: Got {len(playback['events'])} playback events")

        # ========================================
        # Test 2: Event Types Present
        # ========================================
        print("\n--- Test 2: Event Types ---")
        event_types = set(e["type"] for e in playback["events"])
        assert "match_start" in event_types, "Missing match_start event"
        assert "turn_start" in event_types, "Missing turn_start event"
        assert "match_end" in event_types, "Missing match_end event"
        print(f"  PASS: Found event types: {sorted(event_types)}")

        # Must have at least one combat event
        combat_types = {"attack", "damage_taken", "defend", "heal"}
        assert combat_types & event_types, "No combat events found"
        print("  PASS: Combat events present")

        # If match completed with a winner, should have death event
        if match_result["status"] == "complete" and match_result.get("winner_id"):
            assert "death" in event_types, "Winner exists but no death event"
            print("  PASS: Death event present for eliminated champion")

        # ========================================
        # Test 3: Event Ordering and Timing
        # ========================================
        print("\n--- Test 3: Event Ordering ---")
        timestamps = [e["timestamp"] for e in playback["events"]]
        assert timestamps == sorted(timestamps), "Events not in chronological order"
        assert timestamps[0] == 0, "First event should start at timestamp 0"
        print("  PASS: Events in chronological order")

        # First event should be match_start
        assert playback["events"][0]["type"] == "match_start"
        # Last event should be match_end
        assert playback["events"][-1]["type"] == "match_end"
        print("  PASS: Starts with match_start, ends with match_end")

        # All events should have positive durations
        for event in playback["events"]:
            assert event["duration"] > 0, f"Event {event['type']} has duration {event['duration']}"
        print("  PASS: All events have positive durations")

        # ========================================
        # Test 4: Champion Data in Playback
        # ========================================
        print("\n--- Test 4: Champion Data ---")
        for champ in playback["champions"]:
            assert "id" in champ
            assert "name" in champ
            assert "archetype" in champ
            assert "max_hp" in champ
            assert champ["max_hp"] > 0
        print("  PASS: Champion data complete (id, name, archetype, max_hp)")

        # ========================================
        # Test 5: Match Summary Stats
        # ========================================
        print("\n--- Test 5: Summary Stats ---")
        summary = playback["summary"]
        assert len(summary) >= 2, "Summary should have stats for each champion"
        for cid, stats in summary.items():
            assert "damage_dealt" in stats
            assert "damage_taken" in stats
            assert "healing_done" in stats
            assert "kills" in stats
            assert "actions_taken" in stats
            assert "turns_survived" in stats
            assert stats["actions_taken"] > 0, f"{stats['name']} took no actions"
        print("  PASS: Summary stats complete for all champions")

        # Total damage dealt should be positive
        total_damage = sum(s["damage_dealt"] for s in summary.values())
        assert total_damage > 0, "No damage dealt in the match"
        print(f"  PASS: Total damage dealt: {total_damage:.0f}")

        # ========================================
        # Test 6: Sprite Endpoint
        # ========================================
        print("\n--- Test 6: Sprite System ---")
        for arch in ["tank", "assassin", "mage", "ranger", "support"]:
            resp = await client.get(f"/api/sprites/{arch}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["archetype"] == arch
            assert "<svg" in data["svg"]
            assert "<rect" in data["svg"]
        print("  PASS: All 5 archetype sprites generate valid SVG")

        # Invalid archetype
        resp = await client.get("/api/sprites/ninja")
        assert resp.status_code == 404
        print("  PASS: Invalid archetype returns 404")

        # ========================================
        # Test 7: HTML Playback Viewer
        # ========================================
        print("\n--- Test 7: HTML Playback Viewer ---")
        resp = await client.get(f"/api/playback/{match_id}/watch")
        assert resp.status_code == 200
        html = resp.text
        assert "BYTE WARS" in html
        assert "arena" in html
        assert "playNextEvent" in html  # Animation sequencer
        assert "setSpeed" in html       # Speed controls
        assert "summary" in html.lower()  # Match summary
        assert match_id in html
        print("  PASS: HTML viewer renders with arena, animations, controls, summary")

        # Check sprites are embedded
        assert "<svg" in html
        assert "<rect" in html
        print("  PASS: SVG sprites embedded in viewer")

        # Check playback data is embedded
        assert "PLAYBACK" in html
        assert "match_start" in html
        print("  PASS: Playback data embedded in viewer")

        # ========================================
        # Test 8: Shareable Link
        # ========================================
        print("\n--- Test 8: Shareable Link ---")
        resp = await client.get(f"/api/playback/{match_id}/share")
        assert resp.status_code == 200
        share = resp.json()
        assert share["match_id"] == match_id
        assert "/watch" in share["playback_url"]
        assert share["data_url"].endswith(match_id)
        print(f"  PASS: Share link: {share['playback_url']}")

        # ========================================
        # Test 9: Error Cases
        # ========================================
        print("\n--- Test 9: Error Cases ---")

        # Non-existent match
        resp = await client.get("/api/playback/fake-id-999")
        assert resp.status_code == 404
        print("  PASS: 404 for non-existent match")

        # Pending match (create but don't start)
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids[:2],
        })
        pending_id = resp.json()["id"]
        resp = await client.get(f"/api/playback/{pending_id}")
        assert resp.status_code == 400
        print("  PASS: 400 for pending match (not yet complete)")

        resp = await client.get(f"/api/playback/{pending_id}/watch")
        assert resp.status_code == 400
        print("  PASS: 400 for pending match viewer")

        # ========================================
        # Test 10: 4-Way Match Playback
        # ========================================
        print("\n--- Test 10: 4-Way Match Playback ---")
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids,
        })
        match_4way_id = resp.json()["id"]
        resp = await client.post(f"/api/matches/{match_4way_id}/start")
        assert resp.status_code == 200

        resp = await client.get(f"/api/playback/{match_4way_id}")
        assert resp.status_code == 200
        playback_4way = resp.json()
        assert len(playback_4way["champions"]) == 4
        assert len(playback_4way["events"]) > 0
        print(f"  PASS: 4-way playback: {len(playback_4way['events'])} events, "
              f"{len(playback_4way['summary'])} champions in summary")

        # Viewer should work too
        resp = await client.get(f"/api/playback/{match_4way_id}/watch")
        assert resp.status_code == 200
        assert "BYTE WARS" in resp.text
        print("  PASS: 4-way match viewer renders")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 5 Playback & Visualization Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 5 TESTS PASSED")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n  FAIL: {e}")
        print("\n" + "=" * 60)
        print("RESULT: SOME TESTS FAILED")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n  ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("RESULT: TESTS ERRORED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
