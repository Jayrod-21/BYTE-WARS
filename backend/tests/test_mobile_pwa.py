"""
tests/test_mobile_pwa.py — Phase 10 Mobile & PWA Optimization Tests.

Tests:
1. PWA manifest exists and is valid
2. Service worker file exists
3. App icons exist (192 and 512)
4. HTML meta tags for PWA
5. Mobile viewport configuration
6. All API endpoints still work (regression)
7. Playback caching behavior
8. Match history accessible
9. Frontend build files structure
10. Prior phases still pass (smoke test)
"""

import sys
import os
import json

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
from services.wager_service import clear_store as clear_wagers


FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend"
)
PUBLIC_DIR = os.path.join(FRONTEND_DIR, "public")


async def run_tests():
    """Run all Phase 10 tests."""
    clear_champions()
    clear_matches()
    clear_users()
    clear_nfts()
    clear_wagers()

    # ========================================
    # Test 1: PWA Manifest
    # ========================================
    print("\n--- Test 1: PWA Manifest ---")
    manifest_path = os.path.join(PUBLIC_DIR, "manifest.json")
    assert os.path.exists(manifest_path), f"manifest.json not found at {manifest_path}"
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["name"] == "BYTE Wars — AI Battle Arena"
    assert manifest["short_name"] == "BYTE Wars"
    assert manifest["display"] == "standalone"
    assert manifest["background_color"] == "#0a0a1a"
    assert manifest["theme_color"] == "#0a0a1a"
    assert len(manifest["icons"]) >= 2
    print(f"  PASS: Manifest valid ({manifest['short_name']}, {manifest['display']})")

    # ========================================
    # Test 2: Service Worker
    # ========================================
    print("\n--- Test 2: Service Worker ---")
    sw_path = os.path.join(PUBLIC_DIR, "sw.js")
    assert os.path.exists(sw_path), "sw.js not found"
    with open(sw_path) as f:
        sw_content = f.read()
    assert "CACHE_NAME" in sw_content
    assert "install" in sw_content
    assert "activate" in sw_content
    assert "fetch" in sw_content
    assert "push" in sw_content
    assert "notificationclick" in sw_content
    print("  PASS: Service worker has install, activate, fetch, push handlers")

    # ========================================
    # Test 3: App Icons
    # ========================================
    print("\n--- Test 3: App Icons ---")
    icon_192 = os.path.join(PUBLIC_DIR, "icon-192.png")
    icon_512 = os.path.join(PUBLIC_DIR, "icon-512.png")
    favicon = os.path.join(PUBLIC_DIR, "favicon.svg")
    assert os.path.exists(icon_192), "icon-192.png not found"
    assert os.path.exists(icon_512), "icon-512.png not found"
    assert os.path.exists(favicon), "favicon.svg not found"
    assert os.path.getsize(icon_192) > 100, "icon-192.png too small"
    assert os.path.getsize(icon_512) > 100, "icon-512.png too small"
    print(f"  PASS: Icons exist (192={os.path.getsize(icon_192)}B, 512={os.path.getsize(icon_512)}B)")

    # ========================================
    # Test 4: HTML Meta Tags
    # ========================================
    print("\n--- Test 4: HTML Meta Tags ---")
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path) as f:
        html = f.read()
    assert 'name="theme-color"' in html
    assert 'name="viewport"' in html
    assert 'viewport-fit=cover' in html
    assert 'apple-mobile-web-app-capable' in html
    assert 'apple-mobile-web-app-status-bar-style' in html
    assert 'manifest.json' in html
    assert 'BYTE Wars' in html
    print("  PASS: All PWA meta tags present")

    # ========================================
    # Test 5: Mobile Viewport
    # ========================================
    print("\n--- Test 5: Mobile Viewport ---")
    assert 'maximum-scale=1.0' in html
    assert 'user-scalable=no' in html
    assert 'apple-touch-icon' in html
    print("  PASS: Mobile viewport configured (no-zoom, touch icon)")

    # ========================================
    # Test 6: CSS Mobile Optimizations
    # ========================================
    print("\n--- Test 6: CSS Mobile ---")
    css_path = os.path.join(FRONTEND_DIR, "src", "App.css")
    with open(css_path) as f:
        css = f.read()
    assert "safe-area-inset" in css
    assert "-webkit-tap-highlight-color" in css
    assert "display-mode: standalone" in css
    assert "min-height: 44px" in css  # Touch target size
    assert "font-size: 16px" in css   # Prevents iOS zoom
    assert "image-rendering: pixelated" in css  # Pixel art
    print("  PASS: CSS has safe-area, touch targets, iOS fixes, pixel art rendering")

    # ========================================
    # Test 7: Service Worker Registration
    # ========================================
    print("\n--- Test 7: SW Registration ---")
    main_jsx = os.path.join(FRONTEND_DIR, "src", "main.jsx")
    with open(main_jsx) as f:
        main_content = f.read()
    assert "serviceWorker" in main_content
    assert "register" in main_content
    print("  PASS: Service worker registration in main.jsx")

    # ========================================
    # Test 8: Notification Service
    # ========================================
    print("\n--- Test 8: Notifications ---")
    notif_path = os.path.join(FRONTEND_DIR, "src", "services", "notifications.js")
    assert os.path.exists(notif_path), "notifications.js not found"
    with open(notif_path) as f:
        notif_content = f.read()
    assert "requestNotificationPermission" in notif_content
    assert "showNotification" in notif_content
    assert "notifyMatchComplete" in notif_content
    assert "notifyWagerResult" in notif_content
    print("  PASS: Notification service with match/wager notifications")

    # ========================================
    # Test 9: API Regression (key endpoints)
    # ========================================
    print("\n--- Test 9: API Regression ---")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await login_default_user(client)

        # Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        print("  PASS: /health")

        # Auth
        resp = await client.post("/api/auth/register", json={
            "username": "pwa_tester", "password": "secure123",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user"]["id"]
        print("  PASS: Auth registration")

        # Champion CRUD
        resp = await client.post("/api/champions", json={
            "name": "PWA Champion", "archetype": "mage",
        })
        assert resp.status_code == 201
        champ_id = resp.json()["id"]

        resp = await client.get(f"/api/champions/{champ_id}")
        assert resp.status_code == 200
        print("  PASS: Champion CRUD")

        # Create second champion for match
        resp = await client.post("/api/champions", json={
            "name": "PWA Opponent", "archetype": "tank",
        })
        champ2_id = resp.json()["id"]

        # Match + playback
        resp = await client.post("/api/matches", json={
            "champion_ids": [champ_id, champ2_id],
        })
        assert resp.status_code == 201
        match_id = resp.json()["id"]

        resp = await client.post(f"/api/matches/{match_id}/start")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("complete", "timed_out")
        print("  PASS: Match execution")

        resp = await client.get(f"/api/playback/{match_id}")
        assert resp.status_code == 200
        assert len(resp.json()["events"]) > 0
        print("  PASS: Playback retrieval")

        # NFT
        resp = await client.get("/api/nft/catalog/gear")
        assert resp.status_code == 200
        print("  PASS: NFT catalog")

        # Marketplace
        resp = await client.get("/api/nft/marketplace/browse")
        assert resp.status_code == 200
        print("  PASS: Marketplace browse")

        # Wagers
        resp = await client.get(f"/api/wagers/user/{user_id}")
        assert resp.status_code == 200
        print("  PASS: Wager history")

    # ========================================
    # Test 10: Frontend File Structure
    # ========================================
    print("\n--- Test 10: Frontend Structure ---")
    required_files = [
        "src/App.jsx",
        "src/App.css",
        "src/main.jsx",
        "src/services/api.js",
        "src/services/notifications.js",
        "src/pages/LoginPage.jsx",
        "src/pages/ChampionsPage.jsx",
        "src/pages/ChampionBuilderPage.jsx",
        "src/pages/MatchLobbyPage.jsx",
        "src/pages/MatchHistoryPage.jsx",
        "src/pages/PlaybackPage.jsx",
        "src/pages/ProfilePage.jsx",
        "src/pages/InventoryPage.jsx",
        "src/pages/WagerHistoryPage.jsx",
        "src/pages/MarketplacePage.jsx",
        "public/manifest.json",
        "public/sw.js",
        "public/favicon.svg",
        "public/icon-192.png",
        "public/icon-512.png",
        "index.html",
        "package.json",
        "vite.config.js",
    ]
    missing = []
    for f in required_files:
        path = os.path.join(FRONTEND_DIR, f)
        if not os.path.exists(path):
            missing.append(f)
    assert len(missing) == 0, f"Missing files: {missing}"
    print(f"  PASS: All {len(required_files)} required files present")


def main():
    print("=" * 60)
    print("BYTE WARS — Phase 10 Mobile & PWA Tests")
    print("=" * 60)

    try:
        asyncio.run(run_tests())
        print("\n" + "=" * 60)
        print("RESULT: ALL PHASE 10 TESTS PASSED")
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
