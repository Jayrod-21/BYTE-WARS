"""
services/auth_service.py — JWT authentication service for BYTE Wars.

Handles user registration, login, and token management:
- Password hashing with bcrypt
- JWT token generation and validation
- In-memory user store (Phase 6, replaced with DB later)
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt


# JWT configuration
_jwt_secret_env = os.getenv("JWT_SECRET")
if _jwt_secret_env:
    JWT_SECRET = _jwt_secret_env
else:
    # Dev-only: generate a random secret. In production, JWT_SECRET must be set.
    import secrets as _secrets
    JWT_SECRET = _secrets.token_urlsafe(64)
    import logging
    logging.warning("JWT_SECRET not set — using random dev secret. Set JWT_SECRET in production!")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# In-memory user store (replaced with DB in later phases)
_users_store: dict[str, dict] = {}


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, username: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user's UUID.
        username: The user's display name.

    Returns:
        Encoded JWT string.
    """
    payload = {
        "sub": user_id,
        "username": username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decode and validate a JWT token.

    Returns:
        The token payload dict, or None if invalid/expired.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def register_user(username: str, password: str) -> dict:
    """
    Register a new user.

    Args:
        username: Unique username (3-50 chars).
        password: Password (min 6 chars).

    Returns:
        User data dict (without password hash).

    Raises:
        ValueError: If username taken or validation fails.
    """
    if len(username) < 3 or len(username) > 50:
        raise ValueError("Username must be 3-50 characters.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    # Check uniqueness
    for user in _users_store.values():
        if user["username"].lower() == username.lower():
            raise ValueError(f"Username '{username}' is already taken.")

    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "wallet_address": None,
    }
    _users_store[user_id] = user_data

    return {
        "id": user_id,
        "username": username,
        "created_at": user_data["created_at"],
    }


def login_user(username: str, password: str) -> dict:
    """
    Authenticate a user and return a JWT token.

    Args:
        username: The username to authenticate.
        password: The password to verify.

    Returns:
        Dict with token and user info.

    Raises:
        ValueError: If credentials are invalid.
    """
    user = None
    for u in _users_store.values():
        if u["username"].lower() == username.lower():
            user = u
            break

    if user is None:
        raise ValueError("Invalid username or password.")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid username or password.")

    token = create_token(user["id"], user["username"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
        },
    }


def get_user(user_id: str) -> dict | None:
    """Get user by ID (without password hash)."""
    user = _users_store.get(user_id)
    if user is None:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
        "wallet_address": user.get("wallet_address"),
    }


def clear_store():
    """Clear user store. Used by tests."""
    _users_store.clear()
