"""
tests/test_wager_system.py — Phase 8 Wagering System Tests.

Tests:
1. Wallet creation and balance
2. Place wager on pending match
3. Wager validation (amount, champion, duplicate)
4. Cancel wager before match start
5. Escrow lock on match start
6. Payout distribution to winner
7. Refund on timed-out match
8. Odds calculation
9. User wager history
10. Match wagers API
11. Airdrop endpoint
12. Full wager lifecycle (place → lock → fight → payout)
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
    """Run all Phase 8 tests."""
    clear_champions()
    clear_matches()
    clear_users()
    clear_nfts()
    clear_wagers()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # Setup: create champions for testing
        champ_ids = []
        for name, arch in [("Wager Tank", "tank"), ("Wager Assassin", "assassin"),
                           ("Wager Mage", "mage")]:
            resp = await client.post("/api/champions", json={
                "name": name, "archetype": arch,
            })
            assert resp.status_code == 201
            champ_ids.append(resp.json()["id"])

        # Setup: create a user
        resp = await client.post("/api/auth/register", json={
            "username": "bettor1", "password": "secure123",
        })
        assert resp.status_code == 201
        user1_id = resp.json()["user"]["id"]

        resp = await client.post("/api/auth/register", json={
            "username": "bettor2", "password": "secure123",
        })
        assert resp.status_code == 201
        user2_id = resp.json()["user"]["id"]

        wallet1 = f"devnet_{user1_id[:8]}"
        wallet2 = f"devnet_{user2_id[:8]}"

        # ========================================
        # Test 1: Wallet Creation & Balance
        # ========================================
        print("\n--- Test 1: Wallet Creation ---")
        resp = await client.get(f"/api/wagers/wallet/{wallet1}")
        assert resp.status_code == 200
        wallet_data = resp.json()
        assert wallet_data["balance_sol"] == 100.0
        assert wallet_data["available_sol"] == 100.0
        assert wallet_data["locked_sol"] == 0.0
        print("  PASS: Wallet created with 100 SOL")

        # ========================================
        # Test 2: Place Wager on Pending Match
        # ========================================
        print("\n--- Test 2: Place Wager ---")
        # Create a match first
        resp = await client.post("/api/matches", json={
            "champion_ids": [champ_ids[0], champ_ids[1]],
        })
        assert resp.status_code == 201
        match1_id = resp.json()["id"]

        # Place wager
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user1_id,
            "wallet_address": wallet1,
            "champion_id": champ_ids[0],
            "amount_sol": 1.5,
        })
        assert resp.status_code == 200
        wager1 = resp.json()
        assert wager1["amount_sol"] == 1.5
        assert wager1["status"] == "placed"
        assert wager1["champion_id"] == champ_ids[0]
        assert wager1["tx_hash_place"].startswith("stub_tx_")
        wager1_id = wager1["id"]
        print(f"  PASS: Wager placed ({wager1['amount_sol']} SOL)")

        # Check wallet balance updated
        resp = await client.get(f"/api/wagers/wallet/{wallet1}")
        assert resp.json()["locked_sol"] == 1.5
        assert resp.json()["available_sol"] == 98.5
        print("  PASS: Wallet locked 1.5 SOL")

        # ========================================
        # Test 3: Wager Validation
        # ========================================
        print("\n--- Test 3: Wager Validation ---")

        # Too small
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[0],
            "amount_sol": 0.001,
        })
        assert resp.status_code == 400
        assert "Minimum" in resp.json()["detail"]
        print("  PASS: Minimum wager enforced")

        # Too large
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[0],
            "amount_sol": 200.0,
        })
        assert resp.status_code == 400
        assert "Maximum" in resp.json()["detail"]
        print("  PASS: Maximum wager enforced")

        # Wrong champion
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[2],  # Not in this match
            "amount_sol": 1.0,
        })
        assert resp.status_code == 400
        assert "not in this match" in resp.json()["detail"]
        print("  PASS: Champion not in match rejected")

        # Duplicate wager from same user
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user1_id,
            "wallet_address": wallet1,
            "champion_id": champ_ids[1],
            "amount_sol": 1.0,
        })
        assert resp.status_code == 400
        assert "already have" in resp.json()["detail"]
        print("  PASS: Duplicate wager rejected")

        # Non-existent match
        resp = await client.post("/api/wagers/place", json={
            "match_id": "fake-match-id",
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[0],
            "amount_sol": 1.0,
        })
        assert resp.status_code == 404
        print("  PASS: Non-existent match rejected")

        # ========================================
        # Test 4: Cancel Wager
        # ========================================
        print("\n--- Test 4: Cancel Wager ---")
        # Place a wager to cancel
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[1],
            "amount_sol": 2.0,
        })
        assert resp.status_code == 200
        wager2_id = resp.json()["id"]

        # Cancel it
        resp = await client.post(f"/api/wagers/{wager2_id}/cancel", json={
            "user_id": user2_id,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        print("  PASS: Wager cancelled")

        # Check wallet balance restored
        resp = await client.get(f"/api/wagers/wallet/{wallet2}")
        assert resp.json()["locked_sol"] == 0.0
        print("  PASS: Wallet funds unlocked")

        # Cannot cancel someone else's wager
        resp = await client.post(f"/api/wagers/{wager1_id}/cancel", json={
            "user_id": user2_id,
        })
        assert resp.status_code == 400
        assert "own wagers" in resp.json()["detail"]
        print("  PASS: Cannot cancel other user's wager")

        # ========================================
        # Test 5: Escrow Lock on Match Start
        # ========================================
        print("\n--- Test 5: Escrow Lock ---")
        # Place a fresh wager from user2 (the cancelled one doesn't count)
        resp = await client.post("/api/wagers/place", json={
            "match_id": match1_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[1],
            "amount_sol": 3.0,
        })
        assert resp.status_code == 200

        # Check escrow before match start
        resp = await client.get(f"/api/wagers/escrow/{match1_id}")
        assert resp.status_code == 200
        escrow = resp.json()
        assert escrow["status"] == "open"
        assert escrow["total_pot_sol"] == 4.5  # 1.5 + 3.0
        print(f"  PASS: Escrow open, pot = {escrow['total_pot_sol']} SOL")

        # Start match (locks escrow)
        resp = await client.post(f"/api/matches/{match1_id}/start")
        assert resp.status_code == 200
        match_result = resp.json()
        assert match_result["status"] in ("complete", "timed_out")

        # Check escrow is now resolved
        resp = await client.get(f"/api/wagers/escrow/{match1_id}")
        escrow = resp.json()
        assert escrow["status"] in ("distributed", "refunded")
        print(f"  PASS: Escrow resolved ({escrow['status']})")

        # ========================================
        # Test 6: Payout Distribution
        # ========================================
        print("\n--- Test 6: Payout Check ---")
        resp = await client.get(f"/api/wagers/match/{match1_id}")
        match_wagers = resp.json()
        assert len(match_wagers) >= 2  # At least 2 active wagers (plus 1 cancelled)

        # Check wager statuses
        active_wagers = [w for w in match_wagers if w["status"] != "cancelled"]
        statuses = set(w["status"] for w in active_wagers)

        if match_result["status"] == "complete" and match_result.get("winner_id"):
            # There was a winner
            assert "won" in statuses or "lost" in statuses or "refunded" in statuses
            won_wagers = [w for w in active_wagers if w["status"] == "won"]
            if won_wagers:
                for w in won_wagers:
                    assert w["payout_sol"] > 0
                    assert w["tx_hash_payout"].startswith("stub_tx_")
                print(f"  PASS: {len(won_wagers)} winning wager(s) paid out")
            else:
                # Nobody bet on the winner, all refunded
                refunded = [w for w in active_wagers if w["status"] == "refunded"]
                assert len(refunded) > 0
                print("  PASS: No one bet on winner, all refunded")
        else:
            # Timed out — all refunded
            refunded = [w for w in active_wagers if w["status"] == "refunded"]
            assert len(refunded) == len(active_wagers)
            print("  PASS: Match timed out, all wagers refunded")

        # ========================================
        # Test 7: Refund on Timed-Out Match
        # ========================================
        print("\n--- Test 7: Refund Logic ---")
        # Test the refund logic directly via the service
        from services.wager_service import WagerService
        wager_svc = WagerService()

        # Create a new match and wager
        resp = await client.post("/api/matches", json={
            "champion_ids": [champ_ids[0], champ_ids[2]],
        })
        match2_id = resp.json()["id"]

        resp = await client.post("/api/wagers/place", json={
            "match_id": match2_id,
            "user_id": user1_id,
            "wallet_address": wallet1,
            "champion_id": champ_ids[0],
            "amount_sol": 5.0,
        })
        assert resp.status_code == 200

        # Lock and then refund
        wager_svc.lock_escrow(match2_id)
        refunded = wager_svc.refund_all(match2_id)
        assert len(refunded) == 1
        assert refunded[0].status == "refunded"
        assert refunded[0].payout_sol == 5.0
        print("  PASS: Refund returns full amount")

        # ========================================
        # Test 8: Odds Calculation
        # ========================================
        print("\n--- Test 8: Odds Calculation ---")
        # Create a new match with multiple wagers
        resp = await client.post("/api/matches", json={
            "champion_ids": [champ_ids[0], champ_ids[1]],
        })
        match3_id = resp.json()["id"]

        # User1 bets 2 SOL on champion 0
        resp = await client.post("/api/wagers/place", json={
            "match_id": match3_id,
            "user_id": user1_id,
            "wallet_address": wallet1,
            "champion_id": champ_ids[0],
            "amount_sol": 2.0,
        })
        assert resp.status_code == 200

        # User2 bets 8 SOL on champion 1
        resp = await client.post("/api/wagers/place", json={
            "match_id": match3_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[1],
            "amount_sol": 8.0,
        })
        assert resp.status_code == 200

        # Check odds
        resp = await client.get(f"/api/wagers/odds/{match3_id}")
        assert resp.status_code == 200
        odds = resp.json()
        assert odds["total_pot"] == 10.0
        assert odds["platform_fee_percent"] == 5.0

        odds_by_champ = odds["odds_by_champion"]
        assert len(odds_by_champ) == 2

        # Champion 0 has 2 SOL wagered, so implied odds = 9.5/2 = 4.75x
        champ0_odds = odds_by_champ[champ_ids[0]]
        assert champ0_odds["total_wagered"] == 2.0
        assert champ0_odds["implied_odds"] == 4.75
        print(f"  PASS: Champion 0 odds = {champ0_odds['implied_odds']}x")

        # Champion 1 has 8 SOL wagered, so implied odds = 9.5/8 = 1.19x
        champ1_odds = odds_by_champ[champ_ids[1]]
        assert champ1_odds["total_wagered"] == 8.0
        assert champ1_odds["implied_odds"] == 1.19
        print(f"  PASS: Champion 1 odds = {champ1_odds['implied_odds']}x")

        # ========================================
        # Test 9: User Wager History
        # ========================================
        print("\n--- Test 9: User Wager History ---")
        resp = await client.get(f"/api/wagers/user/{user1_id}")
        assert resp.status_code == 200
        user_wagers = resp.json()
        assert len(user_wagers) >= 3  # At least 3 wagers placed by user1
        # Should be sorted newest first
        if len(user_wagers) >= 2:
            assert user_wagers[0]["created_at"] >= user_wagers[1]["created_at"]
        print(f"  PASS: User has {len(user_wagers)} wagers in history")

        # ========================================
        # Test 10: Match Wagers API
        # ========================================
        print("\n--- Test 10: Match Wagers ---")
        resp = await client.get(f"/api/wagers/match/{match3_id}")
        assert resp.status_code == 200
        match_wagers = resp.json()
        assert len(match_wagers) == 2
        print("  PASS: Match has 2 wagers")

        # Empty match
        resp = await client.get("/api/wagers/match/nonexistent")
        assert resp.status_code == 200
        assert len(resp.json()) == 0
        print("  PASS: Non-existent match returns empty list")

        # ========================================
        # Test 11: Airdrop Endpoint
        # ========================================
        print("\n--- Test 11: Airdrop ---")
        resp = await client.post(f"/api/wagers/wallet/{wallet1}/airdrop", json={
            "amount_sol": 50.0,
        })
        assert resp.status_code == 200
        airdrop = resp.json()
        assert airdrop["airdropped"] == 50.0
        print(f"  PASS: Airdropped 50 SOL (new balance: {airdrop['new_balance']})")

        # ========================================
        # Test 12: Full Wager Lifecycle
        # ========================================
        print("\n--- Test 12: Full Lifecycle ---")
        # Fresh match
        resp = await client.post("/api/matches", json={
            "champion_ids": [champ_ids[0], champ_ids[1]],
        })
        match4_id = resp.json()["id"]

        # Place wagers
        resp = await client.post("/api/wagers/place", json={
            "match_id": match4_id,
            "user_id": user1_id,
            "wallet_address": wallet1,
            "champion_id": champ_ids[0],
            "amount_sol": 10.0,
        })
        assert resp.status_code == 200

        resp = await client.post("/api/wagers/place", json={
            "match_id": match4_id,
            "user_id": user2_id,
            "wallet_address": wallet2,
            "champion_id": champ_ids[1],
            "amount_sol": 10.0,
        })
        assert resp.status_code == 200

        # Verify escrow
        resp = await client.get(f"/api/wagers/escrow/{match4_id}")
        assert resp.json()["total_pot_sol"] == 20.0
        assert resp.json()["status"] == "open"

        # Start match (locks escrow, runs battle, distributes payouts)
        resp = await client.post(f"/api/matches/{match4_id}/start")
        assert resp.status_code == 200
        result = resp.json()

        # Verify escrow resolved
        resp = await client.get(f"/api/wagers/escrow/{match4_id}")
        final_escrow = resp.json()
        assert final_escrow["status"] in ("distributed", "refunded")

        # Verify wagers resolved
        resp = await client.get(f"/api/wagers/match/{match4_id}")
        final_wagers = resp.json()
        resolved_statuses = set(w["status"] for w in final_wagers)
        assert "placed" not in resolved_statuses
        assert "locked" not in resolved_statuses

        if result["status"] == "complete" and result.get("winner_id"):
            winner_id = result["winner_id"]
            # Check that platform fee was applied
            assert final_escrow["platform_fee_sol"] == 1.0  # 5% of 20
            assert final_escrow["net_pot_sol"] == 19.0
            print(f"  PASS: Match complete, winner={result['winner_name']}")
            print(f"  PASS: Platform fee={final_escrow['platform_fee_sol']} SOL, net pot={final_escrow['net_pot_sol']} SOL")
        else:
            print(f"  PASS: Match timed out, all wagers refunded")

        print("  PASS: Full lifecycle complete")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 8 Wagering System Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 8 TESTS PASSED")
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
