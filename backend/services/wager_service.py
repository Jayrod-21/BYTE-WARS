"""
services/wager_service.py — Wagering & Escrow service for BYTE Wars Phase 8.

Handles the complete wager lifecycle:
1. Place wager — user bets SOL on a champion before match starts
2. Lock escrow — all wagers locked when match begins
3. Distribute payout — winner(s) split the pot minus platform fee
4. Refund — all wagers returned if match times out

Solana transactions are simulated with stub tx hashes.
Real Anchor smart contract integration in Phase 11.
"""

import uuid
from datetime import datetime, timezone

from models.wager import (
    Wager,
    WagerStatus,
    EscrowAccount,
    EscrowStatus,
    WalletBalance,
    PLATFORM_FEE_PERCENT,
    MIN_WAGER_SOL,
    MAX_WAGER_SOL,
    generate_stub_tx_hash,
    generate_stub_escrow_address,
)


# In-memory stores
_wagers_store: dict[str, Wager] = {}
_escrows_store: dict[str, EscrowAccount] = {}  # keyed by match_id
_wallets_store: dict[str, WalletBalance] = {}   # keyed by wallet_address


class WagerService:
    """
    Manages wagers, escrow accounts, and payouts.

    Flow:
    1. get_or_create_wallet() — ensure user has a simulated wallet
    2. place_wager() — bet on a champion in a pending match
    3. lock_escrow() — called when match starts
    4. distribute_payouts() — called when match completes (winner determined)
    5. refund_all() — called when match times out
    """

    def get_or_create_wallet(self, wallet_address: str) -> WalletBalance:
        """Get or create a simulated devnet wallet with 100 SOL."""
        if wallet_address not in _wallets_store:
            _wallets_store[wallet_address] = WalletBalance(
                wallet_address=wallet_address,
                balance_sol=100.0,
            )
        return _wallets_store[wallet_address]

    def get_wallet(self, wallet_address: str) -> WalletBalance | None:
        """Get wallet balance."""
        return _wallets_store.get(wallet_address)

    def place_wager(
        self,
        match_id: str,
        user_id: str,
        wallet_address: str,
        champion_id: str,
        amount_sol: float,
        match_status: str,
        match_champion_ids: list[str],
    ) -> Wager:
        """
        Place a wager on a champion in a pending match.

        Args:
            match_id: The match to wager on.
            user_id: The user placing the wager.
            wallet_address: The user's Solana wallet address.
            champion_id: The champion to bet on.
            amount_sol: The wager amount in SOL.
            match_status: Current match status (must be "pending").
            match_champion_ids: List of champion IDs in the match.

        Returns:
            The created Wager object.

        Raises:
            ValueError: If validation fails.
        """
        # Validate match status
        if match_status != "pending":
            raise ValueError("Can only place wagers on pending matches.")

        # Validate champion is in the match
        if champion_id not in match_champion_ids:
            raise ValueError(
                f"Champion '{champion_id}' is not in this match."
            )

        # Validate amount
        if amount_sol < MIN_WAGER_SOL:
            raise ValueError(
                f"Minimum wager is {MIN_WAGER_SOL} SOL."
            )
        if amount_sol > MAX_WAGER_SOL:
            raise ValueError(
                f"Maximum wager is {MAX_WAGER_SOL} SOL."
            )

        # Check wallet balance
        wallet = self.get_or_create_wallet(wallet_address)
        if wallet.available_sol < amount_sol:
            raise ValueError(
                f"Insufficient balance. Available: {wallet.available_sol:.4f} SOL, "
                f"requested: {amount_sol:.4f} SOL."
            )

        # Check for duplicate wager (same user, same match)
        for w in _wagers_store.values():
            if (w.match_id == match_id and w.user_id == user_id
                    and w.status == WagerStatus.PLACED):
                raise ValueError(
                    "You already have an active wager on this match."
                )

        # Create escrow if needed
        if match_id not in _escrows_store:
            _escrows_store[match_id] = EscrowAccount(
                match_id=match_id,
                escrow_address=generate_stub_escrow_address(match_id),
            )

        escrow = _escrows_store[match_id]
        if escrow.status != EscrowStatus.OPEN:
            raise ValueError("Escrow is no longer accepting wagers.")

        # Simulate Solana transfer to escrow
        tx_hash = generate_stub_tx_hash()

        # Lock funds in wallet
        wallet.locked_sol += amount_sol

        # Create wager
        wager = Wager(
            match_id=match_id,
            user_id=user_id,
            wallet_address=wallet_address,
            champion_id=champion_id,
            amount_sol=amount_sol,
            status=WagerStatus.PLACED,
            tx_hash_place=tx_hash,
        )

        _wagers_store[wager.id] = wager

        # Update escrow
        escrow.total_pot_sol += amount_sol
        escrow.wager_ids.append(wager.id)

        return wager

    def cancel_wager(self, wager_id: str, user_id: str) -> Wager:
        """
        Cancel a placed (not yet locked) wager.

        Returns the cancelled wager with funds returned.
        """
        wager = _wagers_store.get(wager_id)
        if wager is None:
            raise ValueError(f"Wager '{wager_id}' not found.")
        if wager.user_id != user_id:
            raise ValueError("You can only cancel your own wagers.")
        if wager.status != WagerStatus.PLACED:
            raise ValueError(
                f"Cannot cancel a wager with status '{wager.status}'."
            )

        # Return funds
        wallet = _wallets_store.get(wager.wallet_address)
        if wallet:
            wallet.locked_sol = max(0, wallet.locked_sol - wager.amount_sol)

        # Update escrow
        escrow = _escrows_store.get(wager.match_id)
        if escrow:
            escrow.total_pot_sol = max(0, escrow.total_pot_sol - wager.amount_sol)
            if wager.id in escrow.wager_ids:
                escrow.wager_ids.remove(wager.id)

        wager.status = WagerStatus.CANCELLED
        wager.resolved_at = datetime.now(timezone.utc).isoformat()
        return wager

    def lock_escrow(self, match_id: str) -> EscrowAccount | None:
        """
        Lock the escrow when a match starts. No more wagers accepted.

        Called automatically by match_service.start_match().
        """
        escrow = _escrows_store.get(match_id)
        if escrow is None:
            return None  # No wagers placed — match can still run

        if escrow.status != EscrowStatus.OPEN:
            return escrow  # Already locked

        escrow.status = EscrowStatus.LOCKED
        escrow.locked_at = datetime.now(timezone.utc).isoformat()

        # Lock all placed wagers
        for wid in escrow.wager_ids:
            wager = _wagers_store.get(wid)
            if wager and wager.status == WagerStatus.PLACED:
                wager.status = WagerStatus.LOCKED

        # Calculate fee
        escrow.platform_fee_sol = round(
            escrow.total_pot_sol * (PLATFORM_FEE_PERCENT / 100), 6
        )
        escrow.net_pot_sol = round(
            escrow.total_pot_sol - escrow.platform_fee_sol, 6
        )

        return escrow

    def distribute_payouts(
        self,
        match_id: str,
        winner_id: str | None,
    ) -> list[Wager]:
        """
        Distribute winnings after a match completes.

        Winning logic:
        - All wagers on the winning champion split the net pot
          proportional to their wager amounts.
        - If no winner (draw), all wagers are refunded.

        Returns list of updated wagers.
        """
        escrow = _escrows_store.get(match_id)
        if escrow is None:
            return []

        if escrow.status not in (EscrowStatus.LOCKED, EscrowStatus.OPEN):
            return []  # Already resolved

        now = datetime.now(timezone.utc).isoformat()
        updated = []

        match_wagers = [
            _wagers_store[wid]
            for wid in escrow.wager_ids
            if wid in _wagers_store
        ]

        if winner_id is None:
            # No winner — refund all
            return self.refund_all(match_id)

        # Separate winners and losers
        winning_wagers = [
            w for w in match_wagers
            if w.champion_id == winner_id and w.status == WagerStatus.LOCKED
        ]
        losing_wagers = [
            w for w in match_wagers
            if w.champion_id != winner_id and w.status == WagerStatus.LOCKED
        ]

        if not winning_wagers:
            # Nobody bet on the winner — refund all
            return self.refund_all(match_id)

        # Calculate proportional payouts for winners
        total_winning_wagered = sum(w.amount_sol for w in winning_wagers)

        for wager in winning_wagers:
            proportion = wager.amount_sol / total_winning_wagered
            payout = round(proportion * escrow.net_pot_sol, 6)
            wager.payout_sol = payout
            wager.status = WagerStatus.WON
            wager.resolved_at = now
            wager.tx_hash_payout = generate_stub_tx_hash()

            # Credit wallet
            wallet = _wallets_store.get(wager.wallet_address)
            if wallet:
                wallet.balance_sol += payout - wager.amount_sol  # net gain
                wallet.locked_sol = max(0, wallet.locked_sol - wager.amount_sol)

            updated.append(wager)

        # Mark losers
        for wager in losing_wagers:
            wager.status = WagerStatus.LOST
            wager.resolved_at = now

            # Deduct from wallet
            wallet = _wallets_store.get(wager.wallet_address)
            if wallet:
                wallet.balance_sol -= wager.amount_sol
                wallet.locked_sol = max(0, wallet.locked_sol - wager.amount_sol)

            updated.append(wager)

        escrow.status = EscrowStatus.DISTRIBUTED
        escrow.resolved_at = now

        return updated

    def refund_all(self, match_id: str) -> list[Wager]:
        """
        Refund all wagers for a timed-out or cancelled match.

        Returns list of refunded wagers.
        """
        escrow = _escrows_store.get(match_id)
        if escrow is None:
            return []

        now = datetime.now(timezone.utc).isoformat()
        updated = []

        for wid in escrow.wager_ids:
            wager = _wagers_store.get(wid)
            if wager is None:
                continue
            if wager.status not in (WagerStatus.PLACED, WagerStatus.LOCKED):
                continue

            wager.status = WagerStatus.REFUNDED
            wager.payout_sol = wager.amount_sol  # Full refund
            wager.resolved_at = now
            wager.tx_hash_payout = generate_stub_tx_hash()

            # Unlock wallet funds
            wallet = _wallets_store.get(wager.wallet_address)
            if wallet:
                wallet.locked_sol = max(0, wallet.locked_sol - wager.amount_sol)

            updated.append(wager)

        escrow.status = EscrowStatus.REFUNDED
        escrow.resolved_at = now

        return updated

    def get_match_wagers(self, match_id: str) -> list[dict]:
        """Get all wagers for a match."""
        return [
            w.to_dict() for w in _wagers_store.values()
            if w.match_id == match_id
        ]

    def get_user_wagers(self, user_id: str) -> list[dict]:
        """Get all wagers for a user, sorted by creation date (newest first)."""
        user_wagers = [
            w.to_dict() for w in _wagers_store.values()
            if w.user_id == user_id
        ]
        user_wagers.sort(key=lambda w: w["created_at"], reverse=True)
        return user_wagers

    def get_escrow(self, match_id: str) -> EscrowAccount | None:
        """Get escrow account for a match."""
        return _escrows_store.get(match_id)

    def get_match_odds(self, match_id: str) -> dict:
        """
        Calculate current betting odds for a match.

        Returns dict of champion_id → {total_wagered, wager_count, implied_odds}.
        """
        escrow = _escrows_store.get(match_id)
        if escrow is None:
            return {}

        odds = {}
        total = escrow.total_pot_sol

        for wid in escrow.wager_ids:
            wager = _wagers_store.get(wid)
            if wager is None or wager.status == WagerStatus.CANCELLED:
                continue
            cid = wager.champion_id
            if cid not in odds:
                odds[cid] = {
                    "champion_id": cid,
                    "total_wagered": 0.0,
                    "wager_count": 0,
                    "implied_odds": 0.0,
                }
            odds[cid]["total_wagered"] += wager.amount_sol
            odds[cid]["wager_count"] += 1

        # Calculate implied odds (payout multiplier if this champion wins)
        for cid, data in odds.items():
            if data["total_wagered"] > 0 and total > 0:
                net = total * (1 - PLATFORM_FEE_PERCENT / 100)
                data["implied_odds"] = round(net / data["total_wagered"], 2)
            data["total_wagered"] = round(data["total_wagered"], 6)

        return odds


def clear_store():
    """Clear all wager stores. Used by tests."""
    _wagers_store.clear()
    _escrows_store.clear()
    _wallets_store.clear()
