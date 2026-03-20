"""
routes/nft.py — NFT inventory, marketplace, and equipment API for BYTE Wars.

Phase 7:
- GET    /nft/inventory/{owner_id}      — Get NFT inventory
- POST   /nft/inventory/{owner_id}/generate — Generate starter inventory
- POST   /nft/mint                       — Mint a specific stub NFT
- POST   /nft/equip-gear                 — Equip gear NFTs to a champion
- POST   /nft/equip-skills              — Equip skill NFTs to a champion
- GET    /nft/catalog/gear               — Browse gear catalog
- GET    /nft/catalog/skills             — Browse skill catalog

Phase 9:
- POST   /nft/transfer                  — Transfer NFT between owners
- POST   /nft/marketplace/list          — List an NFT for sale
- POST   /nft/marketplace/{id}/cancel   — Cancel a listing
- POST   /nft/marketplace/{id}/buy      — Purchase a listed NFT
- GET    /nft/marketplace/browse        — Browse marketplace listings
- GET    /nft/marketplace/listing/{id}  — Get listing details
- GET    /nft/{nft_id}/detail           — Get NFT detail page
- GET    /nft/chests/{owner_id}         — Get user's loot chests
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.nft_service import NFTService
from models.nft import GEAR_CATALOG, SKILL_CATALOG
from routes.champion import _champions_store


router = APIRouter(prefix="/nft", tags=["NFT"])
_service = NFTService()


class MintRequest(BaseModel):
    owner_id: str
    catalog_name: str
    nft_type: str = Field(default="gear", description="'gear' or 'skill'")


class EquipRequest(BaseModel):
    champion_id: str
    nft_ids: list[str]
    owner_id: str


@router.get("/inventory/{owner_id}")
async def get_inventory(owner_id: str) -> list[dict]:
    """Get all NFT items owned by a user."""
    return _service.get_inventory(owner_id)


@router.post("/inventory/{owner_id}/generate")
async def generate_inventory(owner_id: str) -> list[dict]:
    """Generate a starter inventory of stub NFTs for testing."""
    return _service.generate_inventory(owner_id)


@router.post("/mint")
async def mint_nft(data: MintRequest) -> dict:
    """Mint a specific stub NFT from the catalog."""
    result = _service.mint_stub_nft(data.owner_id, data.catalog_name, data.nft_type)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item '{data.catalog_name}' not found in {data.nft_type} catalog",
        )
    return result


@router.post("/equip-gear")
async def equip_gear(data: EquipRequest) -> dict:
    """Equip NFT gear items to a champion's gear slots."""
    champion = _champions_store.get(data.champion_id)
    if champion is None:
        raise HTTPException(status_code=404, detail="Champion not found")

    updated, errors = _service.equip_gear_to_champion(champion, data.nft_ids, data.owner_id)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    _champions_store[data.champion_id] = updated
    return {"status": "ok", "gear_slots": updated["gear_slots"]}


@router.post("/equip-skills")
async def equip_skills(data: EquipRequest) -> dict:
    """Equip NFT skill items to a champion's skill slots."""
    champion = _champions_store.get(data.champion_id)
    if champion is None:
        raise HTTPException(status_code=404, detail="Champion not found")

    updated, errors = _service.equip_skills_to_champion(champion, data.nft_ids, data.owner_id)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    _champions_store[data.champion_id] = updated
    return {"status": "ok", "skill_slots": updated["skill_slots"]}


@router.get("/catalog/gear")
async def get_gear_catalog() -> list[dict]:
    """Browse available gear items in the catalog."""
    return GEAR_CATALOG


@router.get("/catalog/skills")
async def get_skill_catalog() -> list[dict]:
    """Browse available skill items in the catalog."""
    return SKILL_CATALOG


# --- Wallet Connection ---

class WalletLinkRequest(BaseModel):
    user_id: str
    wallet_address: str = Field(..., min_length=32, max_length=64)


@router.post("/wallet/link")
async def link_wallet(data: WalletLinkRequest) -> dict:
    """
    Link a Solana wallet address to a user account.

    In Phase 7 this is a simple mapping. Phase 8+ will verify
    wallet ownership via signature challenge.
    """
    from services.auth_service import _users_store
    user = _users_store.get(data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user["wallet_address"] = data.wallet_address
    return {
        "status": "ok",
        "user_id": data.user_id,
        "wallet_address": data.wallet_address,
    }


# =============================================
# Phase 9: NFT Transfer
# =============================================

class TransferRequest(BaseModel):
    nft_id: str
    from_owner: str
    to_owner: str


@router.post("/transfer")
async def transfer_nft(data: TransferRequest) -> dict:
    """Transfer an NFT from one owner to another."""
    try:
        nft = _service.transfer_nft(data.nft_id, data.from_owner, data.to_owner)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return nft.to_dict()


# =============================================
# Phase 9: Marketplace
# =============================================

class ListNFTRequest(BaseModel):
    nft_id: str
    seller_id: str
    price_sol: float = Field(..., gt=0)


class BuyNFTRequest(BaseModel):
    buyer_id: str
    buyer_wallet: str


class CancelListingRequest(BaseModel):
    seller_id: str


@router.post("/marketplace/list")
async def create_listing(data: ListNFTRequest) -> dict:
    """List an NFT for sale on the marketplace."""
    try:
        listing = _service.create_listing(data.nft_id, data.seller_id, data.price_sol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return listing.to_dict()


@router.post("/marketplace/{listing_id}/cancel")
async def cancel_listing(listing_id: str, data: CancelListingRequest) -> dict:
    """Cancel a marketplace listing."""
    try:
        listing = _service.cancel_listing(listing_id, data.seller_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return listing.to_dict()


@router.post("/marketplace/{listing_id}/buy")
async def buy_listing(listing_id: str, data: BuyNFTRequest) -> dict:
    """Purchase an NFT from the marketplace."""
    try:
        listing, nft = _service.purchase_listing(listing_id, data.buyer_id, data.buyer_wallet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "listing": listing.to_dict(),
        "nft": nft.to_dict(),
    }


@router.get("/marketplace/browse")
async def browse_marketplace(
    nft_type: str | None = None,
    rarity: str | None = None,
    archetype: str | None = None,
) -> list[dict]:
    """Browse active marketplace listings with optional filters."""
    return _service.browse_listings(
        nft_type=nft_type,
        rarity=rarity,
        archetype=archetype,
    )


@router.get("/marketplace/listing/{listing_id}")
async def get_listing(listing_id: str) -> dict:
    """Get details of a specific listing."""
    listing = _service.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing.to_dict()


# =============================================
# Phase 9: NFT Detail & Loot Chests
# =============================================

@router.get("/{nft_id}/detail")
async def get_nft_detail(nft_id: str) -> dict:
    """Get full NFT detail including marketplace history."""
    detail = _service.get_nft_detail(nft_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="NFT not found")
    return detail


@router.get("/chests/{owner_id}")
async def get_user_chests(owner_id: str) -> list[dict]:
    """Get all loot chests for a user."""
    return _service.get_user_chests(owner_id)
