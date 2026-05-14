"""
seed.py — Dev-only seed data for BYTE Wars.

When BW_SEED=true (default in BW_ENV=dev), populates the in-memory stores
on startup with a deterministic test playground:
- Users: alice, bob (password "test1234")
- Wallets: devnet_alice, devnet_bob with 100 SOL each
- NFT starter inventory for each user
- 2 champions per user (tank + assassin)
- 3 cross-user marketplace listings per user

Idempotent: re-runs as a no-op once alice exists in the user store.
"""

import logging
import os


logger = logging.getLogger(__name__)


SEED_USERS = [
    {"username": "alice", "password": "test1234"},
    {"username": "bob",   "password": "test1234"},
]

SEED_STARTING_SOL = 100.0
SEED_LISTING_PRICES = [5.0, 8.0, 12.0]


def should_seed() -> bool:
    """True when seeding is requested. Defaults on for BW_ENV=dev."""
    flag = os.getenv("BW_SEED")
    if flag is not None:
        return flag.strip().lower() in ("1", "true", "yes", "on")
    return os.getenv("BW_ENV", "dev").lower() == "dev"


def run_seed() -> None:
    """Populate stores with a usable test playground. Safe to re-run."""
    if not should_seed():
        return

    # Local imports — seed runs after process is fully bootstrapped, so
    # circular imports during module load aren't a risk.
    from services.auth_service import _users_store, register_user
    from services.nft_service import NFTService, _inventory_store, _listings_store
    from services.wager_service import WagerService
    from services.champion_service import ChampionService
    from routes.champion import _champions_store

    for user in _users_store.values():
        if user["username"].lower() == "alice":
            logger.info("[seed] alice already exists — skipping")
            return

    nft_service = NFTService()
    wager_service = WagerService()
    champion_service = ChampionService()

    user_ids: dict[str, str] = {}

    for spec in SEED_USERS:
        username = spec["username"]
        result = register_user(username, spec["password"])
        user_id = result["id"]
        user_ids[username] = user_id

        wallet_address = f"devnet_{username}"
        _users_store[user_id]["wallet_address"] = wallet_address
        wallet = wager_service.get_or_create_wallet(wallet_address)
        wallet.balance_sol = SEED_STARTING_SOL
        wallet.locked_sol = 0.0

        nft_service.generate_inventory(user_id)

        for archetype, suffix in (("tank", "T"), ("assassin", "A")):
            data = champion_service.build_champion_data(
                name=f"{username.upper()}-{suffix}",
                archetype=archetype,
                system_prompt=(
                    "open with the highest damage action; "
                    "fall back to heal when HP < 30%"
                ),
                owner_wallet=wallet_address,
            )
            _champions_store[str(data["id"])] = data

    for username in user_ids:
        seller_id = user_ids[username]
        items = _inventory_store.get(seller_id, [])
        for nft, price in zip(items[: len(SEED_LISTING_PRICES)], SEED_LISTING_PRICES):
            try:
                nft_service.create_listing(nft.id, seller_id, price)
            except ValueError as e:
                logger.warning("[seed] failed to list %s: %s", nft.id, e)

    logger.warning(
        "[seed] playground ready — log in as alice/test1234 or bob/test1234. "
        "users=%d champions=%d listings=%d",
        len(user_ids), len(_champions_store), len(_listings_store),
    )
