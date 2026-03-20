"""
routes/auth.py — Authentication API endpoints for BYTE Wars.

- POST /auth/register — Create a new user account
- POST /auth/login    — Authenticate and receive JWT token
- GET  /auth/me       — Get current user info (requires token)
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from services.auth_service import (
    register_user,
    login_user,
    get_user,
    decode_token,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str | None = None
    wallet_address: str | None = None


async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Dependency: Extract and validate JWT from Authorization header.

    Expects: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]  # Strip "Bearer "
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user(payload["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest) -> dict:
    """Register a new user account."""
    try:
        user_data = register_user(data.username, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Auto-login after registration
    result = login_user(data.username, data.password)
    return result


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest) -> dict:
    """Authenticate and receive a JWT token."""
    try:
        result = login_user(data.username, data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    """Get the current authenticated user's info."""
    return user
