"""
main.py — FastAPI entry point for BYTE Wars.

This is the main application file that sets up the FastAPI server with:
- Health check endpoint (GET /health) — verifies API, DB, and Redis are running
- Database table creation on startup
- CORS middleware for frontend communication

Phase 1: Health check endpoint.
Phase 3: Champion CRUD endpoints (POST, GET, PATCH, LIST).
Phase 4: Match orchestration endpoints (POST, GET, START).
Phase 5: Playback & visualization endpoints (playback data, HTML viewer, sprites).
"""

import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes.champion import router as champion_router
from routes.match import router as match_router
from routes.playback import router as playback_router, sprite_router
from routes.auth import router as auth_router
from routes.nft import router as nft_router
from routes.wager import router as wager_router


# --- Application Lifespan ---
# Create database tables on startup, clean up on shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Create all database tables defined by our SQLAlchemy models.
    Shutdown: Dispose of the database engine connection pool.
    """
    # Import models so SQLAlchemy knows about them when creating tables
    import models  # noqa: F401

    # Try to create tables — if DB isn't available, log warning and continue
    # (the /health endpoint will report DB status)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.warning(f"Could not connect to database on startup: {e}")
        logging.warning("Tables will be created when database becomes available.")

    try:
        from seed import run_seed
        run_seed()
    except Exception as e:
        import logging
        logging.warning(f"Seed run failed: {e}")

    yield  # App runs here

    try:
        await engine.dispose()
    except Exception:
        pass


# --- Create FastAPI App ---
app = FastAPI(
    title="BYTE Wars — AI Battle Arena",
    description="Battle engine API for AI champion combat with Solana wagering",
    version="0.1.0",
    lifespan=lifespan,
)

# --- CORS Middleware ---
# CORS_ORIGINS is a comma-separated allowlist (e.g.
# "https://bytewars.example.com,https://www.bytewars.example.com").
# In dev (BW_ENV=dev or unset), localhost frontends are allowed by default.
# In any other BW_ENV the env var is required — wildcard origins paired with
# allow_credentials=True is rejected by browsers and silently exposes the
# API to any origin.
def _resolve_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    if os.getenv("BW_ENV", "dev").lower() == "dev":
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    raise RuntimeError(
        "CORS_ORIGINS must be set (comma-separated allowlist) when BW_ENV != 'dev'."
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

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

    Returns:
        JSON with status of each service component.
    """
    health = {
        "status": "healthy",
        "api": "up",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check PostgreSQL connection
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["database"] = "up"
    except Exception as e:
        health["database"] = f"down: {str(e)}"
        health["status"] = "degraded"

    # Check Redis connection
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
        await r.aclose()
        health["redis"] = "up"
    except Exception as e:
        health["redis"] = f"down: {str(e)}"
        health["status"] = "degraded"

    return health
