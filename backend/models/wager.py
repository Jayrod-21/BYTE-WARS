"""
models/wager.py — Wager & Escrow data models for BYTE Wars Phase 8.

Defines the wager lifecycle:
1. User places a wager on a champion before the match starts
2. Wager is locked in escrow when the match starts
3. On match completion: winner takes the pot minus platform fee
4. On match timeout: all wagers are refunded

Solana integration is stubbed — simulated wallets and transactions
are used until Anchor smart contract is deployed in production.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WagerStatus(str, Enum):
    """Wager lifecycle states."""
    PLACED = "placed"           # Wager submitted, not yet locked
    LOCKED = "locked"           # Escrow locked when match starts
    WON = "won"                 # Wager won — payout distributed
    LOST = "lost"               # Wager lost — funds forfeited
    REFUNDED = "refunded"       # Match timed out — funds returned
    CANCELLED = "cancelled"     # Wager cancelled before match start


class EscrowStatus(str, Enum):
    """Escrow account states."""
    OPEN = "open"               # Accepting wagers
    LOCKED = "locked"           # Match started, no more wagers
    DISTRIBUTED = "distributed" # Payouts sent
    REFUNDED = "refunded"       # All wagers refunded


# Platform fee: 5% of total pot
PLATFORM_FEE_PERCENT = 5.0
# Minimum wager in SOL
MIN_WAGER_SOL = 0.01
# Maximum wager in SOL
MAX_WAGER_SOL = 100.0


@dataclass
class Wager:
    """A single user's wager on a champion in a match."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str = ""
    user_id: str = ""
    wallet_address: str = ""
    champion_id: str = ""           # The champion they're betting on
    amount_sol: float = 0.0         # Wager amount in SOL
    status: str = WagerStatus.PLACED
    payout_sol: float = 0.0         # Amount paid out (if won)
    tx_hash_place: str = ""         # Solana tx hash for placement (stub)
    tx_hash_payout: str = ""        # Solana tx hash for payout (stub)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "user_id": self.user_id,
            "wallet_address": self.wallet_address,
            "champion_id": self.champion_id,
            "amount_sol": self.amount_sol,
            "status": self.status,
            "payout_sol": self.payout_sol,
            "tx_hash_place": self.tx_hash_place,
            "tx_hash_payout": self.tx_hash_payout,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


@dataclass
class EscrowAccount:
    """
    Simulated Solana escrow account for a match.

    In production, this would be a PDA (Program Derived Address)
    managed by an Anchor smart contract. For Phase 8 we simulate
    the escrow logic in Python.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str = ""
    status: str = EscrowStatus.OPEN
    total_pot_sol: float = 0.0
    platform_fee_sol: float = 0.0
    net_pot_sol: float = 0.0        # total_pot - platform_fee
    escrow_address: str = ""        # Simulated PDA address
    wager_ids: list = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    locked_at: str = ""
    resolved_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "status": self.status,
            "total_pot_sol": self.total_pot_sol,
            "platform_fee_sol": self.platform_fee_sol,
            "net_pot_sol": self.net_pot_sol,
            "escrow_address": self.escrow_address,
            "wager_count": len(self.wager_ids),
            "created_at": self.created_at,
            "locked_at": self.locked_at,
            "resolved_at": self.resolved_at,
        }


def generate_stub_tx_hash() -> str:
    """Generate a fake Solana transaction hash for testing."""
    return f"stub_tx_{uuid.uuid4().hex[:16]}"


def generate_stub_escrow_address(match_id: str) -> str:
    """Generate a fake PDA escrow address for testing."""
    import hashlib
    h = hashlib.sha256(f"escrow:{match_id}".encode()).hexdigest()[:44]
    return h


@dataclass
class WalletBalance:
    """Simulated wallet balance for devnet testing."""
    wallet_address: str = ""
    balance_sol: float = 100.0      # Start with 100 SOL on devnet
    locked_sol: float = 0.0         # Amount locked in active escrows

    @property
    def available_sol(self) -> float:
        return self.balance_sol - self.locked_sol
