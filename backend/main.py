"""
main.py — FastAPI entry point for BYTE Wars.

This is the main application file that sets up the FastAPI server with:
- Health check endpoint (GET /health) — verifies API, DB, and Redis are running
- Database table creation on startup
- CORS middleware for frontend communication
- Security headers middleware
- Rate limiting middleware

Phase 1: Health check endpoint.
Phase 3: Champion CRUD endpoints (POST, GET, PATCH, LIST).
Phase 4: Match orchestration endpoints (POST, GET, START).
Phase 5: Playback & visualization endpoints (playback data, HTML viewer, sprites).
Phase 11: Production hardening (security headers, CORS lockdown, rate limiting).
"""

import os
import time
import logging
from collections import defaultdict
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from database import engine, Base
from routes.champion import router as champion_router
from routes.match import router as match_router
from routes.playback import router as playback_router, sprite_router
from routes.auth import router as auth_router
from routes.nft import router as nft_router
from routes.wager import router as wager_router

# --- Logging Setup ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("byte_wars")


# --- Environment ---
ENV = os.getenv("BYTE_WARS_ENV", "development")  # development | staging | production
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")


# --- Rate Limiter ---
class RateLimiter:
    """Simple in-memory rate limiter (per IP)."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        hits = self._hits[client_ip]
        # Remove expired entries
        self._hits[client_ip] = [t for t in hits if now - t < self.window]
        if len(self._hits[client_ip]) >= self.max_requests:
            return False
        self._hits[client_ip].append(now)
        return True


# Different rate limits for different endpoint types
_general_limiter = RateLimiter(max_requests=120, window_seconds=60)
_auth_limiter = RateLimiter(max_requests=10, window_seconds=60)


# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# --- Rate Limiting Middleware ---
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests per client IP."""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Stricter limit for auth endpoints
        if "/auth/" in path:
            if not _auth_limiter.is_allowed(client_ip):
                return Response(
                    content='{"detail":"Too many requests. Try again later."}',
                    status_code=429,
                    media_type="application/json",
                )
        else:
            if not _general_limiter.is_allowed(client_ip):
                return Response(
                    content='{"detail":"Too many requests. Try again later."}',
                    status_code=429,
                    media_type="application/json",
                )

        return await call_next(request)


# --- Request Logging Middleware ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for monitoring."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)

        # Only log API requests (not static assets)
        if request.url.path.startswith("/api") or request.url.path == "/health":
            logger.info(
                f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)"
            )

        return response


# --- Application Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: Create DB tables. Shutdown: Dispose engine."""
    import models  # noqa: F401

    logger.info(f"BYTE Wars starting (env={ENV})")

    # Validate required env vars in production
    if ENV == "production":
        missing = []
        if not os.getenv("JWT_SECRET"):
            missing.append("JWT_SECRET")
        if not os.getenv("ENCRYPTION_KEY"):
            missing.append("ENCRYPTION_KEY")
        if missing:
            logger.error(f"Missing required env vars for production: {missing}")
            raise RuntimeError(f"Missing required env vars: {missing}")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Could not connect to database on startup: {e}")

    yield

    try:
        await engine.dispose()
    except Exception:
        pass
    logger.info("BYTE Wars shutting down")


# --- Create FastAPI App ---
app = FastAPI(
    title="BYTE Wars — AI Battle Arena",
    description="Battle engine API for AI champion combat with Solana wagering",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
)

# --- Middleware Stack (order matters: last added = first executed) ---

# 1. CORS — restrict origins in production
if ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 4. Request logging
app.add_middleware(RequestLoggingMiddleware)

# --- Register API Routes ---
app.include_router(champion_router, prefix="/api")
app.include_router(match_router, prefix="/api")
app.include_router(playback_router, prefix="/api")
app.include_router(sprite_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(nft_router, prefix="/api")
app.include_router(wager_router, prefix="/api")

# --- Redis Connection ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """
    Health check endpoint. Verifies that the API server, PostgreSQL database,
    and Redis cache are all reachable and responding.
    """
    health = {
        "status": "healthy",
        "api": "up",
        "database": "unknown",
        "redis": "unknown",
        "environment": ENV,
    }

    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["database"] = "up"
    except Exception as e:
        health["database"] = f"down: {str(e)}"
        health["status"] = "degraded"

    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
        await r.aclose()
        health["redis"] = "up"
    except Exception as e:
        health["redis"] = f"down: {str(e)}"
        health["status"] = "degraded"

    return health
