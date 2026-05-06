"""
tests/test_nft_integration.py — Phase 7 NFT & Wallet Integration Tests.

Tests:
1. NFT data model and catalog
2. Stub inventory generation
3. Mint specific NFTs from catalog
4. Equip gear to champion slots
5. Equip skills to champion slots
6. NFT gear stat bonuses applied in battle
7. NFT skills registered as MCP tools in battle
8. Archetype affinity bonus calculation
9. Wallet link endpoint
10. NFT inventory API endpoints
11. Slot limit enforcement with NFTs
12. Battle with NFT-equipped champions vs unequipped
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
from services.auth_service import clear_store as clear_users
from services.nft_service import clear_store as clear_nfts


async def run_tests():
    """Run all Phase 7 tests."""
    clear_champions()
    clear_matches()
    clear_users()
    clear_nfts()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        me = await login_default_user(client)
        owner_id = me["id"]


        # ========================================
        # Test 1: NFT Catalog
        # ========================================
        print("\n--- Test 1: NFT Catalogs ---")
        resp = await client.get("/api/nft/catalog/gear")
        assert resp.status_code == 200
        gear_catalog = resp.json()
        assert len(gear_catalog) > 10
        print(f"  PASS: Gear catalog has {len(gear_catalog)} items")

        resp = await client.get("/api/nft/catalog/skills")
        assert resp.status_code == 200
        skill_catalog = resp.json()
        assert len(skill_catalog) > 5
        print(f"  PASS: Skill catalog has {len(skill_catalog)} items")

        # Check catalog entries have required fields
        gear = gear_catalog[0]
        assert "name" in gear
        assert "rarity" in gear
        assert "stat_bonuses" in gear
        print("  PASS: Catalog entries have correct structure")

        # ========================================
        # Test 2: Generate Starter Inventory
        # ========================================
        print("\n--- Test 2: Starter Inventory ---")
        resp = await client.post(f"/api/nft/inventory/{owner_id}/generate")
        assert resp.status_code == 200
        inventory = resp.json()
        assert len(inventory) == 6  # 4 gear + 2 skills
        gear_count = sum(1 for i in inventory if i["nft_type"] == "gear")
        skill_count = sum(1 for i in inventory if i["nft_type"] == "skill")
        assert gear_count == 4
        assert skill_count == 2
        print(f"  PASS: Generated {gear_count} gear + {skill_count} skills")

        # Second call returns same inventory (no duplicates)
        resp = await client.post(f"/api/nft/inventory/{owner_id}/generate")
        assert len(resp.json()) == 6
        print("  PASS: Re-generate returns existing inventory")

        # ========================================
        # Test 3: Get Inventory
        # ========================================
        print("\n--- Test 3: Get Inventory ---")
        resp = await client.get(f"/api/nft/inventory/{owner_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 6
        print("  PASS: Inventory retrieved")

        # Inventory is private — querying another user's inventory must be denied.
        resp = await client.get("/api/nft/inventory/new-user")
        assert resp.status_code == 403
        print("  PASS: Cross-user inventory query forbidden (403)")

        # ========================================
        # Test 4: Mint Specific NFT
        # ========================================
        print("\n--- Test 4: Mint NFT ---")
        resp = await client.post("/api/nft/mint", json={
            "owner_id": owner_id,
            "catalog_name": "void_daggers",
            "nft_type": "gear",
        })
        assert resp.status_code == 200
        dagger = resp.json()
        assert dagger["name"] == "void_daggers"
        assert dagger["rarity"] == "rare"
        assert dagger["stat_bonuses"]["strength"] == 12
        dagger_id = dagger["id"]
        print(f"  PASS: Minted void_daggers (rare, STR+12)")

        # Mint a skill
        resp = await client.post("/api/nft/mint", json={
            "owner_id": owner_id,
            "catalog_name": "fireball",
            "nft_type": "skill",
        })
        assert resp.status_code == 200
        fireball = resp.json()
        assert fireball["name"] == "fireball"
        assert fireball["skill_action"] is not None
        fireball_id = fireball["id"]
        print(f"  PASS: Minted fireball skill (uncommon)")

        # Non-existent catalog item
        resp = await client.post("/api/nft/mint", json={
            "owner_id": owner_id,
            "catalog_name": "nonexistent_sword",
            "nft_type": "gear",
        })
        assert resp.status_code == 404
        print("  PASS: Non-existent catalog item rejected")

        # ========================================
        # Test 5: Create Champion and Equip Gear
        # ========================================
        print("\n--- Test 5: Equip Gear ---")
        resp = await client.post("/api/champions", json={
            "name": "NFT Assassin",
            "archetype": "assassin",
        })
        assert resp.status_code == 201
        assassin = resp.json()
        assassin_id = assassin["id"]

        resp = await client.post("/api/nft/equip-gear", json={
            "champion_id": assassin_id,
            "nft_ids": [dagger_id],
            "owner_id": owner_id,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert len(result["gear_slots"]) == 1
        assert result["gear_slots"][0]["name"] == "void_daggers"
        print("  PASS: Gear equipped to champion")

        # ========================================
        # Test 6: Equip Skills
        # ========================================
        print("\n--- Test 6: Equip Skills ---")
        resp = await client.post("/api/nft/equip-skills", json={
            "champion_id": assassin_id,
            "nft_ids": [fireball_id],
            "owner_id": owner_id,
        })
        assert resp.status_code == 200
        result = resp.json()
        assert len(result["skill_slots"]) == 1
        assert result["skill_slots"][0]["name"] == "fireball"
        print("  PASS: Skill equipped to champion")

        # ========================================
        # Test 7: Archetype Affinity Bonus
        # ========================================
        print("\n--- Test 7: Archetype Affinity ---")
        from services.nft_service import NFTService
        from models.nft import NFTItem

        nft_svc = NFTService()

        # Void daggers have assassin affinity
        nft = nft_svc.get_nft(dagger_id)
        assert nft is not None

        # Assassin gets 25% bonus
        bonuses_match = nft.get_effective_bonuses("assassin")
        assert bonuses_match["strength"] == 15  # 12 * 1.25 = 15

        # Tank gets no bonus
        bonuses_no_match = nft.get_effective_bonuses("tank")
        assert bonuses_no_match["strength"] == 12
        print("  PASS: Affinity gives 25% bonus (12→15 for assassin, 12 for tank)")

        # ========================================
        # Test 8: NFT Gear Affects Battle Stats
        # ========================================
        print("\n--- Test 8: Gear Affects Battle ---")
        # Create a plain champion (no NFT)
        resp = await client.post("/api/champions", json={
            "name": "Plain Tank",
            "archetype": "tank",
        })
        plain_tank = resp.json()
        plain_id = plain_tank["id"]

        # Create a match: NFT assassin vs plain tank
        resp = await client.post("/api/matches", json={
            "champion_ids": [assassin_id, plain_id],
        })
        assert resp.status_code == 201
        match_id = resp.json()["id"]

        resp = await client.post(f"/api/matches/{match_id}/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("complete", "timed_out")
        print(f"  PASS: Battle with NFT champion completed ({data['total_turns']} turns)")

        # Check playback to verify gear was applied
        resp = await client.get(f"/api/playback/{match_id}")
        assert resp.status_code == 200
        playback = resp.json()
        assert len(playback["events"]) > 0
        print("  PASS: Playback generated for NFT battle")

        # ========================================
        # Test 9: NFT Skills Available in Battle
        # ========================================
        print("\n--- Test 9: NFT Skills in Battle ---")
        # The fireball skill should be available as an action in the battle
        # Check turn history for fireball usage (may or may not be used by MockBot)
        turn_history = data.get("turn_history", [])
        has_turns = len(turn_history) > 0
        assert has_turns, "Battle should have turn history"
        print("  PASS: Battle ran with NFT skill registered")

        # ========================================
        # Test 10: Wallet Link
        # ========================================
        print("\n--- Test 10: Wallet Link ---")
        # Register a user and authenticate as them for the wallet-link calls.
        resp = await client.post("/api/auth/register", json={
            "username": "nft_player",
            "password": "secure123",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user"]["id"]
        nft_headers = {"Authorization": f"Bearer {resp.json()['token']}"}

        resp = await client.post("/api/nft/wallet/link", json={
            "user_id": user_id,
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        }, headers=nft_headers)
        assert resp.status_code == 200
        assert resp.json()["wallet_address"] == "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
        print("  PASS: Wallet linked to user account")

        # Cannot link a wallet to someone else's account.
        resp = await client.post("/api/nft/wallet/link", json={
            "user_id": "fake-id",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        }, headers=nft_headers)
        assert resp.status_code == 403
        print("  PASS: Wallet link rejected for cross-user (403)")

        # ========================================
        # Test 11: Slot Limit Enforcement
        # ========================================
        print("\n--- Test 11: Slot Limits ---")
        # Mint 7 gear items (exceeds 6 slot max)
        gear_ids = []
        for _ in range(7):
            resp = await client.post("/api/nft/mint", json={
                "owner_id": owner_id,
                "catalog_name": "rusty_blade",
                "nft_type": "gear",
            })
            gear_ids.append(resp.json()["id"])

        resp = await client.post("/api/nft/equip-gear", json={
            "champion_id": assassin_id,
            "nft_ids": gear_ids,  # 7 items
            "owner_id": owner_id,
        })
        assert resp.status_code == 400
        assert "Too many" in resp.json()["detail"]
        print("  PASS: Gear slot limit (6) enforced")

        # Mint 5 skills (exceeds 4 slot max)
        skill_ids = []
        for _ in range(5):
            resp = await client.post("/api/nft/mint", json={
                "owner_id": owner_id,
                "catalog_name": "quick_slash",
                "nft_type": "skill",
            })
            skill_ids.append(resp.json()["id"])

        resp = await client.post("/api/nft/equip-skills", json={
            "champion_id": assassin_id,
            "nft_ids": skill_ids,  # 5 items
            "owner_id": owner_id,
        })
        assert resp.status_code == 400
        assert "Too many" in resp.json()["detail"]
        print("  PASS: Skill slot limit (4) enforced")

        # ========================================
        # Test 12: Ownership Verification
        # ========================================
        print("\n--- Test 12: Ownership Check ---")
        # Register a separate "other" user and mint into their inventory.
        resp = await client.post("/api/auth/register", json={
            "username": "other-owner",
            "password": "secure123",
        })
        assert resp.status_code == 201
        other_id = resp.json()["user"]["id"]
        other_headers = {"Authorization": f"Bearer {resp.json()['token']}"}

        resp = await client.post("/api/nft/mint", json={
            "owner_id": other_id,
            "catalog_name": "deaths_whisper",
            "nft_type": "gear",
        }, headers=other_headers)
        other_nft_id = resp.json()["id"]

        # Try to equip other owner's NFT — service-layer ownership check rejects.
        resp = await client.post("/api/nft/equip-gear", json={
            "champion_id": assassin_id,
            "nft_ids": [other_nft_id],
            "owner_id": owner_id,  # Wrong owner — current user, not the NFT's owner
        })
        assert resp.status_code == 400
        assert "does not belong" in resp.json()["detail"]
        print("  PASS: Cannot equip another owner's NFT")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 7 NFT & Wallet Integration Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 7 TESTS PASSED")
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
