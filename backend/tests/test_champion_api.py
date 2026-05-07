"""
tests/test_champion_api.py — Phase 3 Champion Builder API Tests.

Tests the full champion CRUD lifecycle:
1. Create champions with all 5 archetypes
2. Verify archetype defaults (stats, base gear)
3. Retrieve champion profiles
4. Update champion fields (name, system_prompt, gear, API key)
5. Enforce rules: no base gear changes, no archetype changes, slot limits
6. API key encryption: stored encrypted, never returned in responses
7. Cross-archetype gear selection
8. List and filter champions

Success criteria:
- All CRUD operations work correctly
- Validation rejects invalid input
- Base gear is immutable
- API keys are encrypted and never exposed
- Slot limits enforced
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
from httpx import ASGITransport

from main import app
from tests._auth import login_default_user
from routes.champion import clear_store


async def run_tests():
    """Run all Phase 3 API tests."""
    # Clear store before each test run
    clear_store()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        await login_default_user(client)


        print("\n--- Test 1: Create Champions (All 5 Archetypes) ---")
        archetypes = ["tank", "assassin", "mage", "ranger", "support"]
        created_ids = []

        for arch in archetypes:
            resp = await client.post("/api/champions", json={
                "name": f"Test {arch.title()}",
                "archetype": arch,
                "system_prompt": f"I am a {arch} champion. Fight strategically.",
            })
            assert resp.status_code == 201, f"Create {arch} failed: {resp.status_code} {resp.text}"
            data = resp.json()
            assert data["archetype"] == arch
            assert data["name"] == f"Test {arch.title()}"
            assert len(data["base_gear"]) > 0, f"{arch} should have base gear"
            assert data["stats"]["health"] > 0
            created_ids.append(data["id"])
            print(f"  PASS: Created {arch} — HP:{data['stats']['health']} "
                  f"STR:{data['stats']['strength']} END:{data['stats']['endurance']} "
                  f"base_gear:{len(data['base_gear'])}")

        print(f"  PASS: All 5 archetypes created successfully")

        # --- Test 2: Verify Archetype Defaults ---
        print("\n--- Test 2: Archetype Stat Defaults ---")
        resp = await client.get(f"/api/champions/{created_ids[0]}")  # Tank
        tank = resp.json()
        assert tank["stats"]["health"] == 150, f"Tank health should be 150, got {tank['stats']['health']}"
        assert tank["stats"]["strength"] == 35
        assert tank["stats"]["endurance"] == 75
        print("  PASS: Tank stats correct (150 HP, 35 STR, 75 END)")

        resp = await client.get(f"/api/champions/{created_ids[1]}")  # Assassin
        assassin = resp.json()
        assert assassin["stats"]["health"] == 80
        assert assassin["stats"]["strength"] == 80
        print("  PASS: Assassin stats correct (80 HP, 80 STR)")

        # --- Test 3: Retrieve Champion ---
        print("\n--- Test 3: GET /champions/{id} ---")
        resp = await client.get(f"/api/champions/{created_ids[0]}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created_ids[0]
        print("  PASS: Champion retrieved by ID")

        # 404 for non-existent champion
        resp = await client.get("/api/champions/nonexistent-id-999")
        assert resp.status_code == 404
        print("  PASS: 404 for non-existent champion")

        # --- Test 4: Update Champion ---
        print("\n--- Test 4: PATCH /champions/{id} ---")
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "name": "IronClad Updated",
            "system_prompt": "New battle strategy: defend first, then strike.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "IronClad Updated"
        assert "defend first" in data["system_prompt"]
        print("  PASS: Name and system_prompt updated")

        # --- Test 5: Update Gear Slots ---
        print("\n--- Test 5: Gear Slot Updates ---")
        new_gear = [
            {"name": "fire_sword", "type": "gear", "stat_bonus": {"strength": 10}},
            {"name": "ice_shield", "type": "gear", "stat_bonus": {"endurance": 8}},
        ]
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "gear_slots": new_gear,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["gear_slots"]) == 2
        print("  PASS: Gear slots updated (2 items)")

        # Base gear should still be intact
        assert len(data["base_gear"]) > 0
        print(f"  PASS: Base gear preserved ({len(data['base_gear'])} items)")

        # --- Test 6: Enforce Slot Limits ---
        print("\n--- Test 6: Slot Limit Enforcement ---")
        too_many_gear = [{"name": f"item_{i}"} for i in range(7)]  # 7 > max 6
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "gear_slots": too_many_gear,
        })
        assert resp.status_code == 422 or resp.status_code == 400, \
            f"Expected 400/422, got {resp.status_code}"
        print("  PASS: Gear slot limit (6) enforced")

        too_many_skills = [{"name": f"skill_{i}"} for i in range(5)]  # 5 > max 4
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "skill_slots": too_many_skills,
        })
        assert resp.status_code == 422 or resp.status_code == 400
        print("  PASS: Skill slot limit (4) enforced")

        # --- Test 7: Base Gear Protection ---
        print("\n--- Test 7: Base Gear Immutability ---")
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={})
        data = resp.json()
        original_base_gear = data["base_gear"]
        # Base gear should never change regardless of updates
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "name": "Still Has Base Gear",
        })
        data = resp.json()
        assert data["base_gear"] == original_base_gear
        print("  PASS: Base gear unchanged after update")

        # --- Test 8: API Key Encryption ---
        print("\n--- Test 8: API Key Handling ---")
        resp = await client.post("/api/champions", json={
            "name": "Key Test Bot",
            "archetype": "ranger",
            "api_key": "sk-test-secret-key-12345",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["has_api_key"] is True
        assert "sk-test" not in str(data), "API key should not appear in response"
        assert "api_key" not in data or data.get("api_key") is None
        key_champ_id = data["id"]
        print("  PASS: API key stored (has_api_key=True) but not exposed")

        # Retrieve — still no key in response
        resp = await client.get(f"/api/champions/{key_champ_id}")
        data = resp.json()
        assert data["has_api_key"] is True
        assert "sk-test" not in str(data)
        print("  PASS: API key never returned in GET response")

        # --- Test 9: Invalid Archetype ---
        print("\n--- Test 9: Input Validation ---")
        resp = await client.post("/api/champions", json={
            "name": "Bad Bot",
            "archetype": "ninja",  # Invalid
        })
        assert resp.status_code == 422
        print("  PASS: Invalid archetype rejected (422)")

        # Empty name
        resp = await client.post("/api/champions", json={
            "name": "",
            "archetype": "tank",
        })
        assert resp.status_code == 422
        print("  PASS: Empty name rejected (422)")

        # --- Test 10: List Champions ---
        print("\n--- Test 10: GET /champions (List) ---")
        resp = await client.get("/api/champions")
        assert resp.status_code == 200
        all_champs = resp.json()
        assert len(all_champs) >= 5  # At least our 5 + key test bot
        print(f"  PASS: Listed {len(all_champs)} champions")

        # Filter by archetype
        resp = await client.get("/api/champions?archetype=tank")
        assert resp.status_code == 200
        tanks = resp.json()
        assert all(c["archetype"] == "tank" for c in tanks)
        print(f"  PASS: Filtered to {len(tanks)} tank(s)")

        # --- Test 11: Cross-Archetype Gear ---
        print("\n--- Test 11: Cross-Archetype Gear Selection ---")
        # A tank champion can equip mage gear (cross-archetype allowed)
        resp = await client.patch(f"/api/champions/{created_ids[0]}", json={
            "gear_slots": [
                {"name": "arcane_staff", "type": "gear", "stat_bonus": {"strength": 10}},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert any(g.get("name") == "arcane_staff" for g in data["gear_slots"])
        print("  PASS: Tank equipped mage gear (cross-archetype allowed)")

        # --- Test 12: Model Selection ---
        print("\n--- Test 12: AI Model Selection ---")
        resp = await client.post("/api/champions", json={
            "name": "GPT Fighter",
            "archetype": "mage",
            "model": "gpt-4o",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["model"] == "gpt-4o"
        print("  PASS: Custom model selection stored")

        # Update model
        resp = await client.patch(f"/api/champions/{data['id']}", json={
            "model": "gemini-pro",
        })
        assert resp.status_code == 200
        assert resp.json()["model"] == "gemini-pro"
        print("  PASS: Model updated via PATCH")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 3 Champion Builder API Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 3 TESTS PASSED")
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
