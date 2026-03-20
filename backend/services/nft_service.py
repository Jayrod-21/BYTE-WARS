"""
services/nft_service.py — NFT inventory and equipment service for BYTE Wars.

Manages NFT items:
- Inventory storage per wallet/user
- Equipping gear and skills to champion slots
- Applying NFT stat bonuses to champion stats for battle
- Registering NFT skill actions as MCP tools
- Generating starter inventories for new users

Phase 7: In-memory storage with stub NFTs.
Phase 9: On-chain NFT verification via Metaplex.
"""

from datetime import datetime, timezone

from models.nft import (
    NFTItem,
    NFTType,
    GEAR_CATALOG,
    SKILL_CATALOG,
    generate_stub_nft,
    generate_starter_inventory,
    generate_loot_chest,
    RARITY_MULTIPLIERS,
    LOOT_DROP_RATES,
    MarketplaceListing,
    ListingStatus,
    LootChestRecord,
)
from engine.archetypes import MAX_GEAR_SLOTS, MAX_SKILL_SLOTS


# In-memory NFT inventory: wallet_or_user_id -> list[NFTItem]
_inventory_store: dict[str, list[NFTItem]] = {}

# NFT lookup by ID for fast access
_nft_lookup: dict[str, NFTItem] = {}

# Marketplace listings
_listings_store: dict[str, MarketplaceListing] = {}

# Loot chest records
_chest_store: dict[str, LootChestRecord] = {}


class NFTService:
    """
    Manages NFT inventory, equipment, and battle integration.
    """

    def get_inventory(self, owner_id: str) -> list[dict]:
        """Get all NFT items owned by a user/wallet."""
        items = _inventory_store.get(owner_id, [])
        return [item.to_dict() for item in items]

    def get_nft(self, nft_id: str) -> NFTItem | None:
        """Look up an NFT by its ID."""
        return _nft_lookup.get(nft_id)

    def generate_inventory(self, owner_id: str) -> list[dict]:
        """
        Generate a starter inventory for a new user.

        Only generates if the user doesn't already have items.

        Returns:
            List of generated NFT item dicts.
        """
        if owner_id in _inventory_store and _inventory_store[owner_id]:
            return [item.to_dict() for item in _inventory_store[owner_id]]

        items = generate_starter_inventory(owner_id)
        _inventory_store[owner_id] = items
        for item in items:
            _nft_lookup[item.id] = item
        return [item.to_dict() for item in items]

    def mint_stub_nft(
        self,
        owner_id: str,
        catalog_name: str,
        nft_type: str = "gear",
    ) -> dict | None:
        """
        Mint a specific stub NFT from the catalog.

        Args:
            owner_id: Owner's ID or wallet address.
            catalog_name: Name of the item in the catalog.
            nft_type: "gear" or "skill".

        Returns:
            The minted NFT dict, or None if not found in catalog.
        """
        catalog = GEAR_CATALOG if nft_type == "gear" else SKILL_CATALOG
        entry = next((e for e in catalog if e["name"] == catalog_name), None)
        if entry is None:
            return None

        nft = generate_stub_nft(entry, nft_type, owner_id)
        if owner_id not in _inventory_store:
            _inventory_store[owner_id] = []
        _inventory_store[owner_id].append(nft)
        _nft_lookup[nft.id] = nft
        return nft.to_dict()

    def equip_gear_to_champion(
        self,
        champion_data: dict,
        nft_ids: list[str],
        owner_id: str,
    ) -> tuple[dict, list[str]]:
        """
        Equip NFT gear items to a champion's gear slots.

        Validates:
        - All NFT IDs exist and belong to the owner
        - All items are gear type
        - Does not exceed MAX_GEAR_SLOTS
        - Base gear is untouched (separate from gear_slots)

        Args:
            champion_data: The champion dict to modify.
            nft_ids: List of NFT IDs to equip.
            owner_id: Owner's ID for ownership verification.

        Returns:
            Tuple of (updated_champion, errors).
        """
        errors = []
        gear_items = []

        if len(nft_ids) > MAX_GEAR_SLOTS:
            errors.append(f"Too many gear items ({len(nft_ids)}). Max is {MAX_GEAR_SLOTS}.")
            return champion_data, errors

        for nft_id in nft_ids:
            nft = _nft_lookup.get(nft_id)
            if nft is None:
                errors.append(f"NFT '{nft_id}' not found.")
                continue
            if nft.owner_wallet != owner_id:
                errors.append(f"NFT '{nft.name}' does not belong to you.")
                continue
            if nft.nft_type != "gear":
                errors.append(f"NFT '{nft.name}' is a skill, not gear.")
                continue
            gear_items.append({
                "nft_id": nft.id,
                "name": nft.name,
                "type": "gear",
                "rarity": nft.rarity,
                "stat_bonus": nft.stat_bonuses,
                "description": nft.description,
            })

        if errors:
            return champion_data, errors

        champion_data["gear_slots"] = gear_items
        return champion_data, []

    def equip_skills_to_champion(
        self,
        champion_data: dict,
        nft_ids: list[str],
        owner_id: str,
    ) -> tuple[dict, list[str]]:
        """
        Equip NFT skill items to a champion's skill slots.

        Args:
            champion_data: The champion dict to modify.
            nft_ids: List of NFT skill IDs to equip.
            owner_id: Owner's ID for verification.

        Returns:
            Tuple of (updated_champion, errors).
        """
        errors = []
        skill_items = []

        if len(nft_ids) > MAX_SKILL_SLOTS:
            errors.append(f"Too many skills ({len(nft_ids)}). Max is {MAX_SKILL_SLOTS}.")
            return champion_data, errors

        for nft_id in nft_ids:
            nft = _nft_lookup.get(nft_id)
            if nft is None:
                errors.append(f"NFT '{nft_id}' not found.")
                continue
            if nft.owner_wallet != owner_id:
                errors.append(f"NFT '{nft.name}' does not belong to you.")
                continue
            if nft.nft_type != "skill":
                errors.append(f"NFT '{nft.name}' is gear, not a skill.")
                continue
            if nft.skill_action is None:
                errors.append(f"NFT '{nft.name}' has no skill action defined.")
                continue
            skill_items.append({
                "nft_id": nft.id,
                "name": nft.name,
                "type": "skill",
                "rarity": nft.rarity,
                "skill_action": nft.skill_action,
                "description": nft.description,
            })

        if errors:
            return champion_data, errors

        champion_data["skill_slots"] = skill_items
        return champion_data, []

    def apply_gear_bonuses(
        self,
        champion_data: dict,
    ) -> dict:
        """
        Calculate effective stats for a champion with NFT gear equipped.

        Applies:
        1. Base archetype stats
        2. Base gear bonuses (permanent)
        3. NFT gear slot bonuses (with archetype affinity)

        Args:
            champion_data: Champion dict with stats, base_gear, gear_slots.

        Returns:
            New stats dict with all bonuses applied.
        """
        stats = dict(champion_data.get("stats", {}))
        archetype = champion_data.get("archetype", "ranger")

        # Apply base gear bonuses
        for gear in champion_data.get("base_gear", []):
            for stat, bonus in gear.get("stat_bonus", {}).items():
                stats[stat] = stats.get(stat, 0) + bonus

        # Apply NFT gear slot bonuses
        for gear in champion_data.get("gear_slots", []):
            nft_id = gear.get("nft_id")
            if nft_id:
                nft = _nft_lookup.get(nft_id)
                if nft:
                    effective = nft.get_effective_bonuses(archetype)
                    for stat, bonus in effective.items():
                        stats[stat] = stats.get(stat, 0) + bonus
            else:
                # Legacy gear without NFT reference
                for stat, bonus in gear.get("stat_bonus", {}).items():
                    stats[stat] = stats.get(stat, 0) + bonus

        return stats

    def get_skill_actions(self, champion_data: dict) -> list[dict]:
        """
        Get MCP tool action definitions from equipped NFT skills.

        These get dynamically registered with the ToolRegistry
        before battle starts.

        Args:
            champion_data: Champion dict with skill_slots.

        Returns:
            List of action definition dicts for ToolRegistry.register_tool().
        """
        actions = []
        for skill in champion_data.get("skill_slots", []):
            action = skill.get("skill_action")
            if action:
                actions.append(action)
        return actions


    # =============================================
    # Phase 9: Loot Chests
    # =============================================

    def award_loot_chest(self, match_id: str, winner_id: str) -> LootChestRecord:
        """
        Award a loot chest to a match winner.

        Generates random NFT items based on the loot table
        and adds them to the winner's inventory.

        Args:
            match_id: The match that was won.
            winner_id: The winner's owner ID.

        Returns:
            LootChestRecord with the items.
        """
        items = generate_loot_chest(winner_id)

        # Add to inventory
        if winner_id not in _inventory_store:
            _inventory_store[winner_id] = []
        _inventory_store[winner_id].extend(items)
        for item in items:
            _nft_lookup[item.id] = item

        chest = LootChestRecord(
            match_id=match_id,
            owner_id=winner_id,
            items=[item.to_dict() for item in items],
            opened=True,
        )
        _chest_store[chest.id] = chest
        return chest

    def get_chest(self, chest_id: str) -> LootChestRecord | None:
        """Get a loot chest record by ID."""
        return _chest_store.get(chest_id)

    def get_user_chests(self, owner_id: str) -> list[dict]:
        """Get all loot chests for a user."""
        chests = [
            {
                "id": c.id,
                "match_id": c.match_id,
                "items": c.items,
                "opened": c.opened,
                "created_at": c.created_at,
            }
            for c in _chest_store.values()
            if c.owner_id == owner_id
        ]
        chests.sort(key=lambda c: c["created_at"], reverse=True)
        return chests

    # =============================================
    # Phase 9: NFT Transfer
    # =============================================

    def transfer_nft(
        self,
        nft_id: str,
        from_owner: str,
        to_owner: str,
    ) -> NFTItem:
        """
        Transfer an NFT between owners.

        Args:
            nft_id: The NFT to transfer.
            from_owner: Current owner.
            to_owner: New owner.

        Returns:
            Updated NFTItem.

        Raises:
            ValueError: If NFT not found or ownership mismatch.
        """
        nft = _nft_lookup.get(nft_id)
        if nft is None:
            raise ValueError(f"NFT '{nft_id}' not found.")
        if nft.owner_wallet != from_owner:
            raise ValueError("You don't own this NFT.")

        # Remove from sender's inventory
        if from_owner in _inventory_store:
            _inventory_store[from_owner] = [
                item for item in _inventory_store[from_owner]
                if item.id != nft_id
            ]

        # Add to receiver's inventory
        if to_owner not in _inventory_store:
            _inventory_store[to_owner] = []
        nft.owner_wallet = to_owner
        _inventory_store[to_owner].append(nft)

        return nft

    # =============================================
    # Phase 9: Marketplace
    # =============================================

    def create_listing(
        self,
        nft_id: str,
        seller_id: str,
        price_sol: float,
    ) -> MarketplaceListing:
        """
        List an NFT for sale on the marketplace.

        Args:
            nft_id: The NFT to list.
            seller_id: The seller's owner ID.
            price_sol: Asking price in SOL.

        Returns:
            MarketplaceListing.

        Raises:
            ValueError: If validation fails.
        """
        nft = _nft_lookup.get(nft_id)
        if nft is None:
            raise ValueError(f"NFT '{nft_id}' not found.")
        if nft.owner_wallet != seller_id:
            raise ValueError("You don't own this NFT.")
        if price_sol <= 0:
            raise ValueError("Price must be greater than 0.")

        # Check not already listed
        for listing in _listings_store.values():
            if listing.nft_id == nft_id and listing.status == ListingStatus.ACTIVE:
                raise ValueError("This NFT is already listed for sale.")

        listing = MarketplaceListing(
            nft_id=nft_id,
            seller_id=seller_id,
            price_sol=price_sol,
            nft_snapshot=nft.to_dict(),
        )
        _listings_store[listing.id] = listing
        return listing

    def cancel_listing(self, listing_id: str, seller_id: str) -> MarketplaceListing:
        """Cancel an active listing."""
        listing = _listings_store.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing '{listing_id}' not found.")
        if listing.seller_id != seller_id:
            raise ValueError("You can only cancel your own listings.")
        if listing.status != ListingStatus.ACTIVE:
            raise ValueError(f"Listing is '{listing.status}', not active.")

        listing.status = ListingStatus.CANCELLED
        return listing

    def purchase_listing(
        self,
        listing_id: str,
        buyer_id: str,
        buyer_wallet: str,
    ) -> tuple[MarketplaceListing, NFTItem]:
        """
        Purchase an NFT from the marketplace.

        Transfers the NFT to the buyer and marks listing as sold.
        SOL payment is simulated (real Solana tx in Phase 11).

        Args:
            listing_id: The listing to purchase.
            buyer_id: The buyer's owner ID.
            buyer_wallet: The buyer's wallet address (for balance check).

        Returns:
            Tuple of (updated listing, transferred NFT).

        Raises:
            ValueError: If validation fails.
        """
        listing = _listings_store.get(listing_id)
        if listing is None:
            raise ValueError(f"Listing '{listing_id}' not found.")
        if listing.status != ListingStatus.ACTIVE:
            raise ValueError(f"Listing is '{listing.status}', not active.")
        if listing.seller_id == buyer_id:
            raise ValueError("Cannot buy your own listing.")

        # Check buyer wallet balance (using wager wallet system)
        from services.wager_service import _wallets_store
        wallet = _wallets_store.get(buyer_wallet)
        if wallet and wallet.available_sol < listing.price_sol:
            raise ValueError(
                f"Insufficient balance. Need {listing.price_sol} SOL, "
                f"have {wallet.available_sol} SOL."
            )

        # Transfer NFT
        nft = self.transfer_nft(listing.nft_id, listing.seller_id, buyer_id)

        # Simulate SOL payment
        if wallet:
            wallet.balance_sol -= listing.price_sol
        # Credit seller
        seller_wallet_key = f"devnet_{listing.seller_id[:8]}" if len(listing.seller_id) > 8 else listing.seller_id
        from services.wager_service import WagerService
        ws = WagerService()
        seller_wallet = ws.get_or_create_wallet(seller_wallet_key)
        seller_wallet.balance_sol += listing.price_sol

        # Update listing
        listing.status = ListingStatus.SOLD
        listing.buyer_id = buyer_id
        listing.sold_at = datetime.now(timezone.utc).isoformat()

        return listing, nft

    def get_listing(self, listing_id: str) -> MarketplaceListing | None:
        """Get a marketplace listing by ID."""
        return _listings_store.get(listing_id)

    def browse_listings(
        self,
        nft_type: str | None = None,
        rarity: str | None = None,
        archetype: str | None = None,
        status: str = "active",
    ) -> list[dict]:
        """
        Browse marketplace listings with optional filters.

        Args:
            nft_type: Filter by "gear" or "skill".
            rarity: Filter by rarity tier.
            archetype: Filter by archetype affinity.
            status: Filter by listing status (default "active").

        Returns:
            List of listing dicts sorted by newest first.
        """
        results = []
        for listing in _listings_store.values():
            if listing.status != status:
                continue

            snap = listing.nft_snapshot
            if nft_type and snap.get("nft_type") != nft_type:
                continue
            if rarity and snap.get("rarity") != rarity:
                continue
            if archetype and snap.get("archetype_affinity") != archetype:
                continue

            results.append(listing.to_dict())

        results.sort(key=lambda l: l["created_at"], reverse=True)
        return results

    def get_nft_detail(self, nft_id: str) -> dict | None:
        """
        Get full NFT detail including ownership history.

        Returns enriched NFT data with marketplace status.
        """
        nft = _nft_lookup.get(nft_id)
        if nft is None:
            return None

        detail = nft.to_dict()

        # Find active listing
        active_listing = None
        listing_history = []
        for listing in _listings_store.values():
            if listing.nft_id == nft_id:
                if listing.status == ListingStatus.ACTIVE:
                    active_listing = listing.to_dict()
                listing_history.append({
                    "listing_id": listing.id,
                    "price_sol": listing.price_sol,
                    "status": listing.status,
                    "created_at": listing.created_at,
                    "sold_at": listing.sold_at,
                })

        detail["active_listing"] = active_listing
        detail["listing_history"] = listing_history
        return detail


def clear_store():
    """Clear NFT stores. Used by tests."""
    _inventory_store.clear()
    _nft_lookup.clear()
    _listings_store.clear()
    _chest_store.clear()
