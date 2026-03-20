"""
tests/test_production_hardening.py — Phase 11: Production Hardening Tests

Validates:
1. Security headers on all responses
2. Rate limiting enforcement
3. Auth-protected endpoints reject unauthenticated requests
4. Airdrop blocked in production mode
5. Input sanitization strips HTML/control chars
6. Environment-aware CORS configuration
7. JWT secret generation in dev mode
8. Production env var validation
9. Request logging middleware
10. Docker production config exists
"""

import os
import sys
import json
import re
import time

# Ensure backend is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def header(name):
    print(f"\n--- {name} ---")


# =============================================================
# Test 1: Security Headers Middleware
# =============================================================
header("Test 1: Security Headers Middleware")

from main import SecurityHeadersMiddleware

check("SecurityHeadersMiddleware class exists", SecurityHeadersMiddleware is not None)

# Verify the middleware adds headers by inspecting the class
import inspect
source = inspect.getsource(SecurityHeadersMiddleware)
check("Sets X-Content-Type-Options", "X-Content-Type-Options" in source)
check("Sets X-Frame-Options", "X-Frame-Options" in source)
check("Sets X-XSS-Protection", "X-XSS-Protection" in source)
check("Sets Referrer-Policy", "Referrer-Policy" in source)
check("Sets HSTS in production", "Strict-Transport-Security" in source)


# =============================================================
# Test 2: Rate Limiter Logic
# =============================================================
header("Test 2: Rate Limiter Logic")

from main import RateLimiter

limiter = RateLimiter(max_requests=5, window_seconds=2)
test_ip = "192.168.1.1"

# First 5 requests should pass
for i in range(5):
    check(f"Request {i+1} allowed", limiter.is_allowed(test_ip))

# 6th should be blocked
check("Request 6 blocked", not limiter.is_allowed(test_ip))

# Different IP should still work
check("Different IP allowed", limiter.is_allowed("10.0.0.1"))

# Wait for window to expire
time.sleep(2.1)
check("Request allowed after window expires", limiter.is_allowed(test_ip))


# =============================================================
# Test 3: Auth-Protected Endpoints
# =============================================================
header("Test 3: Auth-Protected Endpoints")

# Check that mutation endpoints have get_current_user dependency
from routes.champion import create_champion, update_champion
from routes.match import create_match, start_match
from routes.wager import place_wager, cancel_wager
from routes.nft import mint_nft, equip_gear, equip_skills, transfer_nft
from routes.nft import create_listing, cancel_listing, buy_listing, link_wallet

# Check function signatures for 'user' parameter (injected by Depends)
for name, fn in [
    ("create_champion", create_champion),
    ("update_champion", update_champion),
    ("create_match", create_match),
    ("start_match", start_match),
    ("place_wager", place_wager),
    ("cancel_wager", cancel_wager),
    ("mint_nft", mint_nft),
    ("equip_gear", equip_gear),
    ("equip_skills", equip_skills),
    ("transfer_nft", transfer_nft),
    ("create_listing", create_listing),
    ("cancel_listing", cancel_listing),
    ("buy_listing", buy_listing),
    ("link_wallet", link_wallet),
]:
    sig = inspect.signature(fn)
    has_user = "user" in sig.parameters
    check(f"{name} requires auth", has_user)


# =============================================================
# Test 4: Airdrop Blocked in Production
# =============================================================
header("Test 4: Airdrop Production Guard")

from routes.wager import airdrop_sol
source_airdrop = inspect.getsource(airdrop_sol)
check("Airdrop checks BYTE_WARS_ENV", "BYTE_WARS_ENV" in source_airdrop)
check("Airdrop returns 403 in production", "403" in source_airdrop)


# =============================================================
# Test 5: Input Sanitization
# =============================================================
header("Test 5: Input Sanitization")

from routes.champion import _sanitize_text

check("Strips HTML tags", _sanitize_text("<script>alert(1)</script>hello") == "alert(1)hello")
check("Strips control chars", _sanitize_text("hello\x00world\x0b") == "helloworld")
check("Preserves normal text", _sanitize_text("My Champion") == "My Champion")
check("Strips and trims", _sanitize_text("  <b>test</b>  ") == "test")


# =============================================================
# Test 6: Environment-Aware CORS
# =============================================================
header("Test 6: Environment-Aware CORS")

main_source_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
with open(main_source_path) as f:
    main_source = f.read()

check("ALLOWED_ORIGINS from env var", "ALLOWED_ORIGINS" in main_source)
check("Production CORS restricts origins", 'allow_origins=ALLOWED_ORIGINS' in main_source)
check("Dev CORS allows all", 'allow_origins=["*"]' in main_source)
check("Production disables docs", 'docs_url="/docs" if ENV != "production" else None' in main_source)


# =============================================================
# Test 7: JWT Secret Security
# =============================================================
header("Test 7: JWT Secret Security")

auth_source_path = os.path.join(os.path.dirname(__file__), "..", "services", "auth_service.py")
with open(auth_source_path) as f:
    auth_source = f.read()

check("Reads JWT_SECRET from env", 'os.getenv("JWT_SECRET")' in auth_source)
check("Dev secret uses token_urlsafe", "token_urlsafe" in auth_source)
check("Warns when using dev secret", "JWT_SECRET not set" in auth_source)
# Make sure there's no hardcoded fallback
check("No hardcoded JWT secret", "super-secret" not in auth_source and "changeme" not in auth_source)


# =============================================================
# Test 8: Encryption Key Security
# =============================================================
header("Test 8: Encryption Key Security")

champ_svc_path = os.path.join(os.path.dirname(__file__), "..", "services", "champion_service.py")
with open(champ_svc_path) as f:
    champ_source = f.read()

check("Reads ENCRYPTION_KEY from env", 'os.getenv("ENCRYPTION_KEY")' in champ_source)
check("Warns when ENCRYPTION_KEY not set", "ENCRYPTION_KEY not set" in champ_source)


# =============================================================
# Test 9: Production Env Var Validation
# =============================================================
header("Test 9: Production Env Var Validation")

check("Validates JWT_SECRET in production", 'os.getenv("JWT_SECRET")' in main_source and "missing" in main_source.lower())
check("Validates ENCRYPTION_KEY in production", 'os.getenv("ENCRYPTION_KEY")' in main_source)
check("Raises on missing env vars", "RuntimeError" in main_source)


# =============================================================
# Test 10: Request Logging Middleware
# =============================================================
header("Test 10: Request Logging Middleware")

from main import RequestLoggingMiddleware

check("RequestLoggingMiddleware exists", RequestLoggingMiddleware is not None)
log_source = inspect.getsource(RequestLoggingMiddleware)
check("Logs request method and path", "request.method" in log_source)
check("Logs response status", "response.status_code" in log_source)
check("Logs duration", "duration" in log_source)


# =============================================================
# Test 11: Rate Limit Middleware Config
# =============================================================
header("Test 11: Rate Limit Config")

from main import _general_limiter, _auth_limiter

check("General limiter: 120 req/min", _general_limiter.max_requests == 120)
check("Auth limiter: 10 req/min", _auth_limiter.max_requests == 10)
check("Auth limiter stricter", _auth_limiter.max_requests < _general_limiter.max_requests)


# =============================================================
# Test 12: Production Docker Config
# =============================================================
header("Test 12: Production Docker Config")

prod_compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.prod.yml")
check("docker-compose.prod.yml exists", os.path.isfile(prod_compose_path))

if os.path.isfile(prod_compose_path):
    with open(prod_compose_path) as f:
        prod_config = f.read()
    check("Sets BYTE_WARS_ENV=production", "BYTE_WARS_ENV=production" in prod_config)
    check("Uses JWT_SECRET env var", "JWT_SECRET" in prod_config)
    check("Uses ENCRYPTION_KEY env var", "ENCRYPTION_KEY" in prod_config)
    check("Multiple workers", "--workers" in prod_config)
    check("No host volume mounts", "volumes: []" in prod_config)
    check("DB port not exposed", 'ports: []' in prod_config)


# =============================================================
# Test 13: Ownership Verification
# =============================================================
header("Test 13: Ownership Verification")

champ_route_path = os.path.join(os.path.dirname(__file__), "..", "routes", "champion.py")
with open(champ_route_path) as f:
    champ_route_source = f.read()

check("Sets owner_user_id on create", 'owner_user_id' in champ_route_source)
check("Checks ownership on update", "do not own" in champ_route_source.lower())


# =============================================================
# Test 14: All Previous Tests Still Pass
# =============================================================
header("Test 14: Existing Tests Regression")

# Run MCP integration tests
import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_mcp_integration.py", "-v", "--tb=short"],
    capture_output=True,
    text=True,
    cwd=os.path.join(os.path.dirname(__file__), ".."),
)
check("MCP integration tests pass", result.returncode == 0)


# =============================================================
# Summary
# =============================================================
print(f"\n{'='*60}")
total = PASS + FAIL
if FAIL == 0:
    print(f"RESULT: ALL PHASE 11 TESTS PASSED ({PASS}/{total})")
else:
    print(f"RESULT: {FAIL} FAILURE(S) ({PASS}/{total} passed)")
print(f"{'='*60}")
