"""
tests/test_auth_and_frontend.py — Phase 6 Auth & Web Interface Tests.

Tests:
1. User registration
2. User login with JWT
3. Protected endpoint (/auth/me)
4. Invalid credentials
5. Duplicate username
6. Token validation
7. Full flow: register → login → create champion → create match → playback
8. Frontend build verification
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


async def run_tests():
    """Run all Phase 6 tests."""
    clear_champions()
    clear_matches()
    clear_users()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # ========================================
        # Test 1: User Registration
        # ========================================
        print("\n--- Test 1: User Registration ---")
        resp = await client.post("/api/auth/register", json={
            "username": "warrior1",
            "password": "secret123",
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "warrior1"
        token = data["token"]
        user_id = data["user"]["id"]
        print(f"  PASS: Registered warrior1 (id: {user_id[:8]})")

        # ========================================
        # Test 2: Login
        # ========================================
        print("\n--- Test 2: Login ---")
        resp = await client.post("/api/auth/login", json={
            "username": "warrior1",
            "password": "secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "warrior1"
        login_token = data["token"]
        print("  PASS: Login successful, token received")

        # ========================================
        # Test 3: Protected Endpoint (GET /auth/me)
        # ========================================
        print("\n--- Test 3: Protected Endpoint ---")
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {login_token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "warrior1"
        assert data["id"] == user_id
        print("  PASS: /auth/me returns user data with valid token")

        # Without token
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401
        print("  PASS: 401 without Authorization header")

        # With invalid token
        resp = await client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token-xyz",
        })
        assert resp.status_code == 401
        print("  PASS: 401 with invalid token")

        # ========================================
        # Test 4: Invalid Credentials
        # ========================================
        print("\n--- Test 4: Invalid Credentials ---")
        resp = await client.post("/api/auth/login", json={
            "username": "warrior1",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        print("  PASS: Wrong password rejected")

        resp = await client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "secret123",
        })
        assert resp.status_code == 401
        print("  PASS: Non-existent user rejected")

        # ========================================
        # Test 5: Duplicate Username
        # ========================================
        print("\n--- Test 5: Duplicate Username ---")
        resp = await client.post("/api/auth/register", json={
            "username": "warrior1",
            "password": "another123",
        })
        assert resp.status_code == 400
        print("  PASS: Duplicate username rejected")

        # ========================================
        # Test 6: Validation Rules
        # ========================================
        print("\n--- Test 6: Validation ---")
        # Username too short
        resp = await client.post("/api/auth/register", json={
            "username": "ab",
            "password": "secret123",
        })
        assert resp.status_code == 422
        print("  PASS: Short username rejected (422)")

        # Password too short
        resp = await client.post("/api/auth/register", json={
            "username": "validname",
            "password": "12345",
        })
        assert resp.status_code == 422
        print("  PASS: Short password rejected (422)")

        # ========================================
        # Test 7: Full Flow — Register → Champion → Match → Playback
        # ========================================
        print("\n--- Test 7: Full User Flow ---")
        # Register a second user
        resp = await client.post("/api/auth/register", json={
            "username": "player2",
            "password": "pass456789",
        })
        assert resp.status_code == 201
        print("  PASS: Second user registered")

        # Create champions
        champ_ids = []
        for arch in ["tank", "assassin"]:
            resp = await client.post("/api/champions", json={
                "name": f"Flow {arch.title()}",
                "archetype": arch,
            })
            assert resp.status_code == 201
            champ_ids.append(resp.json()["id"])
        print(f"  PASS: Created {len(champ_ids)} champions")

        # Create and run match
        resp = await client.post("/api/matches", json={
            "champion_ids": champ_ids,
        })
        assert resp.status_code == 201
        match_id = resp.json()["id"]

        resp = await client.post(f"/api/matches/{match_id}/start")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("complete", "timed_out")
        print("  PASS: Match completed")

        # Get playback
        resp = await client.get(f"/api/playback/{match_id}")
        assert resp.status_code == 200
        assert len(resp.json()["events"]) > 0
        print("  PASS: Playback data retrieved")

        # Get HTML viewer
        resp = await client.get(f"/api/playback/{match_id}/watch")
        assert resp.status_code == 200
        assert "BYTE WARS" in resp.text
        print("  PASS: Full flow complete (register → champion → match → playback)")

        # ========================================
        # Test 8: Frontend Build Verification
        # ========================================
        print("\n--- Test 8: Frontend Build ---")
        dist_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "frontend", "dist"
        )
        assert os.path.exists(dist_path), f"Frontend dist not found at {dist_path}"
        index_html = os.path.join(dist_path, "index.html")
        assert os.path.exists(index_html), "index.html not found in dist"

        with open(index_html) as f:
            html = f.read()
        assert "root" in html  # React mount point
        print("  PASS: Frontend build exists and contains React mount point")

        # Check assets
        assets_path = os.path.join(dist_path, "assets")
        assert os.path.exists(assets_path), "Assets directory not found"
        assets = os.listdir(assets_path)
        has_js = any(f.endswith('.js') for f in assets)
        has_css = any(f.endswith('.css') for f in assets)
        assert has_js, "No JS bundle found"
        assert has_css, "No CSS bundle found"
        print(f"  PASS: Frontend assets present ({len(assets)} files)")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 6 Auth & Web Interface Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 6 TESTS PASSED")
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
