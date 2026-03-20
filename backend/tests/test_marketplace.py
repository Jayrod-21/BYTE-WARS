"""
tests/test_marketplace.py — Phase 9 NFT Marketplace Tests.

Tests:
1. Loot drop rates (rarity distribution)
2. Loot chest generation
3. Loot chest awarded on match win
4. NFT transfer between owners
5. Marketplace listing creation
6. Marketplace listing cancellation
7. Marketplace purchase flow
8. Marketplace browse with filters
9. NFT detail page (with listing history)
10. Cannot buy own listing / insufficient balance
11. Cannot list NFT you don't own
12. Full lifecycle: win → chest → list → sell
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from httpx import ASGITransport

from main import app
from routes.champion import clear_store as clear_champions
from services.match_service import clear_store as clear_matches
from services.auth_service import clear_store as clear_users
from services.nft_service import clear_store as clear_nfts
from services.wager_service import clear_store as clear_wagers


async def run_tests():
    """Run all Phase 9 tests."""
    clear_champions()
    clear_matches()
    clear_users()
    clear_nfts()
    clear_wagers()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # Setup: create users
        resp = await client.post("/api/auth/register", json={
            "username": "seller1", "password": "secure123",
        })
        seller_id = resp.json()["user"]["id"]
        seller_token = resp.json()["token"]
        auth_seller = {"Authorization": f"Bearer {seller_token}"}

        resp = await client.post("/api/auth/register", json={
            "username": "buyer1", "password": "secure123",
        })
        buyer_id = resp.json()["user"]["id"]
        buyer_token = resp.json()["token"]
        auth_buyer = {"Authorization": f"Bearer {buyer_token}"}

        seller_wallet = f"devnet_{seller_id[:8]}"
        buyer_wallet = f"devnet_{buyer_id[:8]}"

        # Setup: give buyer some SOL
        await client.post(f"/api/wagers/wallet/{buyer_wallet}/airdrop", json={"amount_sol": 50.0})

        # Setup: create champions (requires auth)
        resp = await client.post("/api/champions", json={
            "name": "Market Tank", "archetype": "tank",
        }, headers=auth_seller)
        tank_id = resp.json()["id"]

        resp = await client.post("/api/champions", json={
            "name": "Market Assassin", "archetype": "assassin",
        }, headers=auth_seller)
        assassin_id = resp.json()["id"]

        # ========================================
        # Test 1: Loot Drop Rates
        # ========================================
        print("\n--- Test 1: Loot Drop Rates ---")
        from models.nft import roll_loot_rarity, LOOT_DROP_RATES
        counts = {"common": 0, "uncommon": 0, "rare": 0, "legendary": 0}
        for _ in range(1000):
            rarity = roll_loot_rarity()
            counts[rarity] += 1

        # Check rough distribution (within 10% of expected)
        assert counts["common"] > 350, f"Common too low: {counts['common']}"
        assert counts["uncommon"] > 200, f"Uncommon too low: {counts['uncommon']}"
        assert counts["rare"] > 50, f"Rare too low: {counts['rare']}"
        assert counts["legendary"] >= 1, f"No legendaries in 1000 rolls"
        print(f"  PASS: Drop rates: C={counts['common']}, U={counts['uncommon']}, R={counts['rare']}, L={counts['legendary']}")

        # ========================================
        # Test 2: Loot Chest Generation
        # ========================================
        print("\n--- Test 2: Loot Chest Generation ---")
        from models.nft import generate_loot_chest, LOOT_CHEST_SIZE
        chest_items = generate_loot_chest("test-owner")
        assert len(chest_items) == LOOT_CHEST_SIZE
        for item in chest_items:
            assert item.nft_type in ("gear", "skill")
            assert item.rarity in ("common", "uncommon", "rare", "legendary")
            assert item.owner_wallet == "test-owner"
        print(f"  PASS: Generated chest with {len(chest_items)} items")

        # ========================================
        # Test 3: Loot Chest on Match Win
        # ========================================
        print("\n--- Test 3: Chest on Match Win ---")
        resp = await client.post("/api/matches", json={
            "champion_ids": [tank_id, assassin_id],
        }, headers=auth_seller)
        match_id = resp.json()["id"]

        resp = await client.post(f"/api/matches/{match_id}/start", headers=auth_seller)
        assert resp.status_code == 200
        match_result = resp.json()

        if match_result["status"] == "complete" and match_result.get("winner_id"):
            assert match_result.get("loot_chest_id") is not None
            assert len(match_result.get("loot_chest_items", [])) == LOOT_CHEST_SIZE
            print(f"  PASS: Winner got loot chest with {len(match_result['loot_chest_items'])} items")
        else:
            print(f"  PASS: Match timed out (no chest, expected)")

        # ========================================
        # Test 4: NFT Transfer
        # ========================================
        print("\n--- Test 4: NFT Transfer ---")
        # Mint an NFT for seller
        resp = await client.post("/api/nft/mint", json={
            "owner_id": seller_id, "catalog_name": "void_daggers", "nft_type": "gear",
        }, headers=auth_seller)
        nft1_id = resp.json()["id"]
        assert resp.json()["owner_wallet"] == seller_id

        # Transfer to buyer
        resp = await client.post("/api/nft/transfer", json={
            "nft_id": nft1_id, "from_owner": seller_id, "to_owner": buyer_id,
        }, headers=auth_seller)
        assert resp.status_code == 200
        assert resp.json()["owner_wallet"] == buyer_id
        print("  PASS: NFT transferred to buyer")

        # Verify seller no longer has it
        resp = await client.get(f"/api/nft/inventory/{seller_id}")
        seller_nfts = [n for n in resp.json() if n["id"] == nft1_id]
        assert len(seller_nfts) == 0

        # Verify buyer has it
        resp = await client.get(f"/api/nft/inventory/{buyer_id}")
        buyer_nfts = [n for n in resp.json() if n["id"] == nft1_id]
        assert len(buyer_nfts) == 1
        print("  PASS: Inventory updated correctly")

        # Cannot transfer what you don't own
        resp = await client.post("/api/nft/transfer", json={
            "nft_id": nft1_id, "from_owner": seller_id, "to_owner": buyer_id,
        }, headers=auth_seller)
        assert resp.status_code == 400
        print("  PASS: Cannot transfer NFT you don't own")

        # Transfer it back for marketplace tests
        resp = await client.post("/api/nft/transfer", json={
            "nft_id": nft1_id, "from_owner": buyer_id, "to_owner": seller_id,
        }, headers=auth_buyer)
        assert resp.status_code == 200

        # ========================================
        # Test 5: Marketplace Listing
        # ========================================
        print("\n--- Test 5: Create Listing ---")
        resp = await client.post("/api/nft/marketplace/list", json={
            "nft_id": nft1_id, "seller_id": seller_id, "price_sol": 5.0,
        }, headers=auth_seller)
        assert resp.status_code == 200
        listing = resp.json()
        listing_id = listing["id"]
        assert listing["price_sol"] == 5.0
        assert listing["status"] == "active"
        assert listing["nft_snapshot"]["name"] == "void_daggers"
        print(f"  PASS: Listed void_daggers for 5.0 SOL")

        # Cannot list same NFT twice
        resp = await client.post("/api/nft/marketplace/list", json={
            "nft_id": nft1_id, "seller_id": seller_id, "price_sol": 10.0,
        }, headers=auth_seller)
        assert resp.status_code == 400
        assert "already listed" in resp.json()["detail"]
        print("  PASS: Cannot double-list same NFT")

        # ========================================
        # Test 6: Cancel Listing
        # ========================================
        print("\n--- Test 6: Cancel Listing ---")
        # Mint another NFT to list and cancel
        resp = await client.post("/api/nft/mint", json={
            "owner_id": seller_id, "catalog_name": "rusty_blade", "nft_type": "gear",
        }, headers=auth_seller)
        nft2_id = resp.json()["id"]

        resp = await client.post("/api/nft/marketplace/list", json={
            "nft_id": nft2_id, "seller_id": seller_id, "price_sol": 1.0,
        }, headers=auth_seller)
        listing2_id = resp.json()["id"]

        resp = await client.post(f"/api/nft/marketplace/{listing2_id}/cancel", json={
            "seller_id": seller_id,
        }, headers=auth_seller)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        print("  PASS: Listing cancelled")

        # Cannot cancel someone else's listing
        resp = await client.post(f"/api/nft/marketplace/{listing_id}/cancel", json={
            "seller_id": buyer_id,
        }, headers=auth_buyer)
        assert resp.status_code == 400
        assert "own listings" in resp.json()["detail"]
        print("  PASS: Cannot cancel other's listing")

        # ========================================
        # Test 7: Purchase Flow
        # ========================================
        print("\n--- Test 7: Purchase ---")
        resp = await client.post(f"/api/nft/marketplace/{listing_id}/buy", json={
            "buyer_id": buyer_id, "buyer_wallet": buyer_wallet,
        }, headers=auth_buyer)
        assert resp.status_code == 200
        result = resp.json()
        assert result["listing"]["status"] == "sold"
        assert result["nft"]["owner_wallet"] == buyer_id
        print("  PASS: NFT purchased successfully")

        # Verify buyer wallet was charged
        resp = await client.get(f"/api/wagers/wallet/{buyer_wallet}")
        assert resp.json()["balance_sol"] < 150  # Started with 150 (100 + 50 airdrop)
        print("  PASS: Buyer wallet charged")

        # Verify NFT is in buyer's inventory
        resp = await client.get(f"/api/nft/inventory/{buyer_id}")
        has_nft = any(n["id"] == nft1_id for n in resp.json())
        assert has_nft
        print("  PASS: NFT in buyer's inventory")

        # ========================================
        # Test 8: Browse Marketplace
        # ========================================
        print("\n--- Test 8: Browse Marketplace ---")
        # List a few more items
        for catalog_name, nft_type in [("fireball", "skill"), ("steel_gauntlets", "gear"), ("archmage_tome", "gear")]:
            resp = await client.post("/api/nft/mint", json={
                "owner_id": seller_id, "catalog_name": catalog_name, "nft_type": nft_type,
            }, headers=auth_seller)
            nft_id = resp.json()["id"]
            await client.post("/api/nft/marketplace/list", json={
                "nft_id": nft_id, "seller_id": seller_id, "price_sol": 2.0,
            }, headers=auth_seller)

        # Browse all
        resp = await client.get("/api/nft/marketplace/browse")
        assert resp.status_code == 200
        all_listings = resp.json()
        active_count = len(all_listings)
        assert active_count >= 3
        print(f"  PASS: {active_count} active listings")

        # Filter by type
        resp = await client.get("/api/nft/marketplace/browse?nft_type=skill")
        skill_listings = resp.json()
        assert all(l["nft_snapshot"]["nft_type"] == "skill" for l in skill_listings)
        print(f"  PASS: Filtered to {len(skill_listings)} skill listings")

        # Filter by rarity
        resp = await client.get("/api/nft/marketplace/browse?rarity=rare")
        rare_listings = resp.json()
        assert all(l["nft_snapshot"]["rarity"] == "rare" for l in rare_listings)
        print(f"  PASS: Filtered to {len(rare_listings)} rare listings")

        # Filter by archetype
        resp = await client.get("/api/nft/marketplace/browse?archetype=mage")
        mage_listings = resp.json()
        assert all(l["nft_snapshot"]["archetype_affinity"] == "mage" for l in mage_listings)
        print(f"  PASS: Filtered to {len(mage_listings)} mage listings")

        # ========================================
        # Test 9: NFT Detail Page
        # ========================================
        print("\n--- Test 9: NFT Detail ---")
        resp = await client.get(f"/api/nft/{nft1_id}/detail")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["name"] == "void_daggers"
        assert detail["rarity"] == "rare"
        assert detail["owner_wallet"] == buyer_id  # Was purchased by buyer
        assert "listing_history" in detail
        assert len(detail["listing_history"]) >= 1  # Was listed and sold
        print("  PASS: NFT detail includes listing history")

        # Non-existent NFT
        resp = await client.get("/api/nft/fake-id/detail")
        assert resp.status_code == 404
        print("  PASS: Non-existent NFT returns 404")

        # ========================================
        # Test 10: Purchase Validation
        # ========================================
        print("\n--- Test 10: Purchase Validation ---")
        # Cannot buy own listing
        resp = await client.post("/api/nft/mint", json={
            "owner_id": seller_id, "catalog_name": "deaths_whisper", "nft_type": "gear",
        }, headers=auth_seller)
        own_nft_id = resp.json()["id"]
        resp = await client.post("/api/nft/marketplace/list", json={
            "nft_id": own_nft_id, "seller_id": seller_id, "price_sol": 50.0,
        }, headers=auth_seller)
        own_listing_id = resp.json()["id"]

        resp = await client.post(f"/api/nft/marketplace/{own_listing_id}/buy", json={
            "buyer_id": seller_id, "buyer_wallet": seller_wallet,
        }, headers=auth_seller)
        assert resp.status_code == 400
        assert "own listing" in resp.json()["detail"]
        print("  PASS: Cannot buy own listing")

        # Cannot buy sold listing
        resp = await client.post(f"/api/nft/marketplace/{listing_id}/buy", json={
            "buyer_id": buyer_id, "buyer_wallet": buyer_wallet,
        }, headers=auth_buyer)
        assert resp.status_code == 400
        print("  PASS: Cannot buy already-sold listing")

        # ========================================
        # Test 11: Cannot List What You Don't Own
        # ========================================
        print("\n--- Test 11: Ownership Check ---")
        resp = await client.post("/api/nft/marketplace/list", json={
            "nft_id": nft1_id, "seller_id": seller_id, "price_sol": 5.0,
        }, headers=auth_seller)
        assert resp.status_code == 400
        assert "don't own" in resp.json()["detail"]
        print("  PASS: Cannot list NFT you don't own")

        # ========================================
        # Test 12: Loot Chests API
        # ========================================
        print("\n--- Test 12: Loot Chests API ---")
        # The match winner should have chests
        # Chest is awarded to the champion's owner_user_id (the authenticated user)
        if match_result.get("winner_id"):
            resp = await client.get(f"/api/nft/chests/{seller_id}")
            assert resp.status_code == 200
            chests = resp.json()
            assert len(chests) >= 1
            assert len(chests[0]["items"]) == LOOT_CHEST_SIZE
            print(f"  PASS: Winner has {len(chests)} chest(s)")
        else:
            print("  PASS: No winner, no chests (expected)")

        # No chests for non-winner
        resp = await client.get("/api/nft/chests/nobody")
        assert resp.status_code == 200
        assert len(resp.json()) == 0
        print("  PASS: Non-winner has no chests")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 9 NFT Marketplace Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 9 TESTS PASSED")
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
