"""
routes/wager.py — Wager API endpoints for BYTE Wars Phase 8.

Provides wagering functionality:
- POST   /wagers/place             — Place a wager on a champion in a pending match
- POST   /wagers/{id}/cancel       — Cancel a placed (not locked) wager
- GET    /wagers/match/{match_id}  — Get all wagers for a match
- GET    /wagers/user/{user_id}    — Get wager history for a user
- GET    /wagers/odds/{match_id}   — Get current betting odds for a match
- GET    /wagers/escrow/{match_id} — Get escrow account info
- GET    /wagers/wallet/{address}  — Get wallet balance
- POST   /wagers/wallet/{address}/airdrop — Airdrop devnet SOL (testing)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from routes._authz import (
    get_current_user,
    require_self,
    expected_wallet,
    require_dev_env,
)
from services.wager_service import WagerService
from services.match_service import MatchService


router = APIRouter(prefix="/wagers", tags=["Wagers"])
_wager_service = WagerService()
_match_service = MatchService()


class PlaceWagerRequest(BaseModel):
    """Request to place a wager. user_id and wallet_address must match the
    authenticated principal — they are still accepted in the body for
    backward compat with the existing frontend, but the server validates
    them."""
    match_id: str
    user_id: str
    wallet_address: str
    champion_id: str
    amount_sol: float = Field(..., gt=0, description="Wager amount in SOL")


class CancelWagerRequest(BaseModel):
    """Request to cancel a wager."""
    user_id: str


class AirdropRequest(BaseModel):
    """Request devnet SOL airdrop."""
    amount_sol: float = Field(default=10.0, gt=0, le=100.0)


@router.post("/place")
async def place_wager(
    data: PlaceWagerRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Place a wager on a champion in a pending match.

    The wager amount is locked from the user's wallet balance.
    Wagers can only be placed before the match starts.

    Requires authentication; the body's `user_id` and `wallet_address`
    must match the authenticated principal so a logged-in user cannot
    place wagers on someone else's behalf.
    """
    require_self(data.user_id, user)
    if data.wallet_address != expected_wallet(user):
        raise HTTPException(
            status_code=403,
            detail="wallet_address does not match authenticated user",
        )

    # Look up the match
    match_data = _match_service.get_match(data.match_id)
    if match_data is None:
        raise HTTPException(status_code=404, detail="Match not found.")

    try:
        wager = _wager_service.place_wager(
            match_id=data.match_id,
            user_id=data.user_id,
            wallet_address=data.wallet_address,
            champion_id=data.champion_id,
            amount_sol=data.amount_sol,
            match_status=match_data["status"],
            match_champion_ids=match_data["champion_ids"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return wager.to_dict()


@router.post("/{wager_id}/cancel")
async def cancel_wager(
    wager_id: str,
    data: CancelWagerRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Cancel a placed (not yet locked) wager. Funds are returned.

    Requires authentication; body `user_id` must match the principal."""
    require_self(data.user_id, user)
    try:
        wager = _wager_service.cancel_wager(wager_id, data.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return wager.to_dict()


@router.get("/match/{match_id}")
async def get_match_wagers(match_id: str) -> list[dict]:
    """Get all wagers placed on a match."""
    return _wager_service.get_match_wagers(match_id)


@router.get("/user/{user_id}")
async def get_user_wagers(user_id: str) -> list[dict]:
    """Get wager history for a user, sorted by date (newest first)."""
    return _wager_service.get_user_wagers(user_id)


@router.get("/odds/{match_id}")
async def get_match_odds(match_id: str) -> dict:
    """
    Get current betting odds for a match.

    Returns per-champion totals and implied payout multiplier.
    """
    match_data = _match_service.get_match(match_id)
    if match_data is None:
        raise HTTPException(status_code=404, detail="Match not found.")

    odds = _wager_service.get_match_odds(match_id)
    escrow = _wager_service.get_escrow(match_id)

    return {
        "match_id": match_id,
        "total_pot": escrow.total_pot_sol if escrow else 0.0,
        "platform_fee_percent": 5.0,
        "odds_by_champion": odds,
    }


@router.get("/escrow/{match_id}")
async def get_escrow(match_id: str) -> dict:
    """Get escrow account info for a match."""
    escrow = _wager_service.get_escrow(match_id)
    if escrow is None:
        return {
            "match_id": match_id,
            "status": "none",
            "total_pot_sol": 0.0,
            "wager_count": 0,
        }
    return escrow.to_dict()


@router.get("/wallet/{wallet_address}")
async def get_wallet_balance(wallet_address: str) -> dict:
    """Get wallet balance (simulated devnet)."""
    wallet = _wager_service.get_or_create_wallet(wallet_address)
    return {
        "wallet_address": wallet.wallet_address,
        "balance_sol": wallet.balance_sol,
        "locked_sol": wallet.locked_sol,
        "available_sol": wallet.available_sol,
    }


@router.post("/wallet/{wallet_address}/airdrop")
async def airdrop_sol(
    wallet_address: str,
    data: AirdropRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Airdrop devnet SOL to a wallet — dev-only.

    Returns 404 outside of dev (BW_ENV != "dev") so the route doesn't
    leak its existence in production. The authenticated user can only
    airdrop to their own wallet.
    """
    require_dev_env()
    if wallet_address != expected_wallet(user):
        raise HTTPException(
            status_code=403,
            detail="Can only airdrop to your own wallet",
        )

    wallet = _wager_service.get_or_create_wallet(wallet_address)
    wallet.balance_sol += data.amount_sol

    return {
        "wallet_address": wallet.wallet_address,
        "airdropped": data.amount_sol,
        "new_balance": wallet.balance_sol,
    }
