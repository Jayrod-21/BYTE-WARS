"""
routes/_authz.py — Shared authorization helpers for route modules.

`get_current_user` is the FastAPI dependency that extracts and validates
the JWT from the Authorization header (defined in routes.auth). This
module wraps it with helpers that also enforce ownership: a request
must not act on someone else's user_id, wallet, etc.
"""

import os

from fastapi import HTTPException, Depends

from routes.auth import get_current_user


def require_self(claimed_user_id: str, user: dict) -> None:
    """
    Reject the request if the body-supplied user_id doesn't match the
    authenticated principal. Prevents trivial impersonation when routes
    accept user_id as a request field instead of deriving it from the
    token.
    """
    if claimed_user_id != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="user_id does not match authenticated user",
        )


def expected_wallet(user: dict) -> str:
    """
    Canonical wallet address for a user. Mirrors the frontend convention
    of `devnet_<userId>` when no wallet is linked yet (see
    `frontend/src/services/api.js` and `frontend/src/App.jsx`).
    """
    return user.get("wallet_address") or f"devnet_{user['id']}"


def require_dev_env() -> None:
    """
    Refuse the call when not in dev. Used to gate mock/dev-only routes
    (airdrop, inventory generators) that would be exploitable in prod.
    """
    if os.getenv("BW_ENV", "dev").lower() != "dev":
        raise HTTPException(status_code=404, detail="Not found")


# Re-export so route modules can `from routes._authz import get_current_user`
__all__ = ["get_current_user", "require_self", "expected_wallet", "require_dev_env", "Depends"]
