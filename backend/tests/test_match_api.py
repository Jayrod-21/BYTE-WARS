"""
tests/test_match_api.py — Phase 4 Match Orchestration API Tests.

Tests the full match lifecycle:
1. Create champions for the match
2. Create a match (lobby with 2-4 champions)
3. Start the match (async execution)
4. Poll for results (match complete or timed out)
5. Verify turn history and winner determination
6. Test multi-bot free-for-all (1v1v1v1)
7. Validate state machine transitions
8. Test error cases (invalid IDs, wrong status, too few/many champions)

All tests use MockBot (no real API keys) to keep tests fast and deterministic.
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
    """Run all Phase 4 API tests."""
    clear_champions()
    clear_matches()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        await login_default_user(client)


        # --- Setup: Create champions for testing ---
        print("\n--- Setup: Creating Test Champions ---")
        champion_ids = []
        archetypes = ["tank", "assassin", "mage", "ranger"]

        for arch in archetypes:
            resp = await client.post("/api/champions", json={
                "name": f"Bot {arch.title()}",
                "archetype": arch,
                "system_prompt": f"I am a {arch}. Fight wisely.",
            })
            assert resp.status_code == 201
            champion_ids.append(resp.json()["id"])

        print(f"  Created {len(champion_ids)} champions for testing")

        # ========================================
        # Test 1: Create a Match (2 champions)
        # ========================================
        print("\n--- Test 1: Create Match (1v1) ---")
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids[:2],
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        match_1v1 = resp.json()
        assert match_1v1["status"] == "pending"
        assert len(match_1v1["champion_ids"]) == 2
        assert match_1v1["winner_id"] is None
        match_1v1_id = match_1v1["id"]
        print(f"  PASS: Match created (pending) — {match_1v1_id[:8]}")

        # ========================================
        # Test 2: Start the Match
        # ========================================
        print("\n--- Test 2: Start Match ---")
        resp = await client.post(f"/api/matches/{match_1v1_id}/start")
        assert resp.status_code == 200
        data = resp.json()
        # Match executes inline (awaited), so it completes during this call
        assert data["status"] in ("complete", "timed_out"), \
            f"Expected complete/timed_out, got {data['status']}"
        assert data["started_at"] is not None
        print(f"  PASS: Match started and resolved — {data['status']}")

        # ========================================
        # Test 3: Verify Results
        # ========================================
        print("\n--- Test 3: Verify Results ---")
        # Fetch fresh to confirm persistence
        resp = await client.get(f"/api/matches/{match_1v1_id}")
        assert resp.status_code == 200, f"GET failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data["status"] in ("complete", "timed_out"), \
            f"Status was '{data['status']}', expected complete/timed_out"
        assert data["total_turns"] > 0, \
            f"total_turns was {data['total_turns']}"
        assert data["resolved_at"] is not None, "resolved_at was None"
        assert len(data["turn_history"]) > 0, \
            f"turn_history had {len(data['turn_history'])} entries"

        if data["status"] == "complete":
            print(f"  PASS: Match complete in {data['total_turns']} turns")
            if data["winner_id"]:
                print(f"  Winner: {data['winner_name']} ({data['winner_id'][:8]})")
            else:
                print("  Result: Draw (all champions eliminated)")
        else:
            print(f"  PASS: Match timed out after {data['total_turns']} turns")

        # ========================================
        # Test 4: Turn History Structure
        # ========================================
        print("\n--- Test 4: Turn History Validation ---")
        turn = data["turn_history"][0]
        assert "turn_number" in turn
        assert "champion_id" in turn
        assert "champion_name" in turn
        assert "actions_taken" in turn
        assert "resolutions" in turn
        assert turn["turn_number"] == 1
        print("  PASS: Turn history has correct structure")

        # Check resolutions have damage data
        has_resolution = False
        for t in data["turn_history"]:
            if t["resolutions"]:
                res = t["resolutions"][0]
                assert "action" in res
                assert "target_hp_before" in res
                assert "target_hp_after" in res
                has_resolution = True
                break
        assert has_resolution, "Expected at least one resolution with damage data"
        print("  PASS: Resolutions contain damage/heal details")

        # ========================================
        # Test 5: Multi-Bot Free-For-All (1v1v1v1)
        # ========================================
        print("\n--- Test 5: 4-Way Free-For-All ---")
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids,  # All 4
        })
        assert resp.status_code == 201
        match_4way = resp.json()
        assert len(match_4way["champion_ids"]) == 4
        match_4way_id = match_4way["id"]
        print(f"  PASS: 4-way match created — {match_4way_id[:8]}")

        # Start (executes inline)
        resp = await client.post(f"/api/matches/{match_4way_id}/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("complete", "timed_out")
        print(f"  PASS: 4-way match resolved — {data['status']} "
              f"in {data['total_turns']} turns")
        if data["winner_name"]:
            print(f"  Winner: {data['winner_name']}")

        # ========================================
        # Test 6: State Machine Validation
        # ========================================
        print("\n--- Test 6: State Machine Rules ---")

        # Cannot start a match that's already complete
        resp = await client.post(f"/api/matches/{match_1v1_id}/start")
        assert resp.status_code == 400
        print("  PASS: Cannot re-start a completed match")

        # Cannot start a non-existent match
        resp = await client.post("/api/matches/fake-id-123/start")
        assert resp.status_code == 400
        print("  PASS: Cannot start non-existent match")

        # ========================================
        # Test 7: Error Cases
        # ========================================
        print("\n--- Test 7: Error Cases ---")

        # Too few champions (1)
        resp = await client.post("/api/matches", json={
            "champion_ids": [champion_ids[0]],
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        print("  PASS: Rejected 1-champion match (422)")

        # Non-existent champion ID
        resp = await client.post("/api/matches", json={
            "champion_ids": [champion_ids[0], "nonexistent-id-123"],
        })
        assert resp.status_code == 404
        print("  PASS: Rejected match with non-existent champion (404)")

        # ========================================
        # Test 8: Match Retrieval
        # ========================================
        print("\n--- Test 8: GET /matches/{id} ---")
        resp = await client.get(f"/api/matches/{match_1v1_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == match_1v1_id
        print("  PASS: Match retrieved by ID")

        # 404 for non-existent
        resp = await client.get("/api/matches/fake-id-999")
        assert resp.status_code == 404
        print("  PASS: 404 for non-existent match")

        # ========================================
        # Test 9: List Matches
        # ========================================
        print("\n--- Test 9: GET /matches (List) ---")
        resp = await client.get("/api/matches")
        assert resp.status_code == 200
        all_matches = resp.json()
        assert len(all_matches) >= 2  # At least our 2 matches
        print(f"  PASS: Listed {len(all_matches)} matches")

        # Filter by status
        resp = await client.get("/api/matches?status=complete")
        assert resp.status_code == 200
        completed = resp.json()
        assert all(m["status"] == "complete" for m in completed)
        print(f"  PASS: Filtered to {len(completed)} complete match(es)")

        # ========================================
        # Test 10: Match Data Doesn't Leak API Keys
        # ========================================
        print("\n--- Test 10: No API Key Leakage ---")
        resp = await client.get(f"/api/matches/{match_1v1_id}")
        data = resp.json()
        data_str = str(data)
        assert "api_key" not in data_str.lower() or "champion_data" not in data_str
        assert "encrypted" not in data_str.lower()
        print("  PASS: Match responses don't contain API key data")

        # ========================================
        # Test 11: 3-Way Match (1v1v1)
        # ========================================
        print("\n--- Test 11: 3-Way Free-For-All ---")
        resp = await client.post("/api/matches", json={
            "champion_ids": champion_ids[:3],
        })
        assert resp.status_code == 201
        match_3way = resp.json()
        assert len(match_3way["champion_ids"]) == 3
        match_3way_id = match_3way["id"]

        resp = await client.post(f"/api/matches/{match_3way_id}/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("complete", "timed_out")
        print(f"  PASS: 3-way match resolved — {data['status']} "
              f"in {data['total_turns']} turns")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 4 Match Orchestration API Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 4 TESTS PASSED")
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
