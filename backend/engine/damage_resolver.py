"""
engine/damage_resolver.py — Probabilistic damage resolution for BYTE Wars.

Handles all damage and healing calculations. Every action's outcome is determined
by rolling within the action's damage/heal range, then applying stat modifiers:

- Strength modifier (attacker): damage * (1 + strength / 100)
- Endurance modifier (defender): incoming damage reduced by endurance / 200
- Defense buff: if defender used 'defend' this turn, reduce damage by 30%

Every resolution is logged with full detail for playback reconstruction.
"""

import random
from dataclasses import dataclass


@dataclass
class ResolutionResult:
    """
    The outcome of resolving a single action.

    Contains all the data needed to reconstruct what happened for
    the battle history log and playback system.
    """
    action_name: str        # Which action was used
    attacker_id: str        # Who performed the action
    target_id: str | None   # Who was targeted (None for self-targeting actions)
    raw_roll: int           # The base random roll before modifiers
    modified_damage: float  # Final damage after all modifiers applied
    healing_done: float     # Amount of HP restored (0 if not a heal)
    target_hp_before: float # Target's HP before this action resolved
    target_hp_after: float  # Target's HP after this action resolved
    is_kill: bool           # Whether this action knocked out the target


class DamageResolver:
    """
    Resolves combat actions into concrete outcomes using probabilistic rolls
    and stat-based modifiers.

    Core rules:
    - All damage uses RNG within the action's [min, max] range
    - Strength increases outgoing damage: damage * (1 + strength/100)
    - Endurance reduces incoming damage: damage * (1 - endurance/200)
    - The 'defend' action grants a 30% damage reduction buff for the turn
    """

    def resolve_attack(
        self,
        action: dict,
        attacker_stats: dict,
        defender_stats: dict,
        defender_hp: float,
        defender_is_defending: bool = False,
    ) -> ResolutionResult:
        """
        Resolve an attack action against a defender.

        Args:
            action: The action dictionary (from actions.py)
            attacker_stats: Attacker's stats dict (health, strength, endurance)
            defender_stats: Defender's stats dict
            defender_hp: Defender's current HP before this attack
            defender_is_defending: Whether the defender used 'defend' this turn

        Returns:
            ResolutionResult with all resolution details for the battle log.
        """
        damage_range = action["damage_range"]

        # Step 1: Roll raw damage within the action's range
        raw_roll = random.randint(damage_range[0], damage_range[1])

        # Step 2: Apply attacker's strength modifier
        # Higher strength = more damage: damage * (1 + strength/100)
        strength = attacker_stats.get("strength", 50)
        strength_modified = raw_roll * (1 + strength / 100)

        # Step 3: Apply defender's endurance modifier
        # Higher endurance = less damage taken: damage * (1 - endurance/200)
        endurance = defender_stats.get("endurance", 50)
        endurance_reduction = endurance / 200
        after_endurance = strength_modified * (1 - endurance_reduction)

        # Step 4: Apply defense buff if active (30% reduction)
        if defender_is_defending:
            final_damage = after_endurance * (1 - 0.30)
        else:
            final_damage = after_endurance

        # Round to 1 decimal place for cleaner logs
        final_damage = round(max(final_damage, 1.0), 1)  # Minimum 1 damage

        # Step 5: Apply damage to defender's HP
        hp_after = round(max(defender_hp - final_damage, 0), 1)

        return ResolutionResult(
            action_name=action["name"],
            attacker_id="",  # Set by caller
            target_id="",    # Set by caller
            raw_roll=raw_roll,
            modified_damage=final_damage,
            healing_done=0,
            target_hp_before=defender_hp,
            target_hp_after=hp_after,
            is_kill=(hp_after <= 0),
        )

    def resolve_heal(
        self,
        action: dict,
        healer_stats: dict,
        current_hp: float,
        max_hp: float,
    ) -> ResolutionResult:
        """
        Resolve a healing action on self.

        Args:
            action: The heal action dictionary
            healer_stats: The healer's stats dict
            current_hp: Current HP before healing
            max_hp: Maximum HP (cannot heal above this)

        Returns:
            ResolutionResult with healing details for the battle log.
        """
        heal_range = action["heal_range"]

        # Step 1: Roll raw healing within range
        raw_roll = random.randint(heal_range[0], heal_range[1])

        # Step 2: Apply endurance modifier to healing
        # Higher endurance = more effective heals
        endurance = healer_stats.get("endurance", 50)
        modified_heal = raw_roll * (1 + endurance / 200)
        modified_heal = round(modified_heal, 1)

        # Step 3: Cap healing at max HP
        hp_after = round(min(current_hp + modified_heal, max_hp), 1)
        actual_heal = round(hp_after - current_hp, 1)

        return ResolutionResult(
            action_name=action["name"],
            attacker_id="",  # Set by caller
            target_id="",    # Set by caller (self)
            raw_roll=raw_roll,
            modified_damage=0,
            healing_done=actual_heal,
            target_hp_before=current_hp,
            target_hp_after=hp_after,
            is_kill=False,
        )

    def resolve_defend(self, defender_id: str, defender_hp: float) -> ResolutionResult:
        """
        Resolve a defend action. The actual damage reduction is applied when
        the defender is attacked (via defender_is_defending flag).

        Args:
            defender_id: ID of the champion using defend
            defender_hp: Current HP of the defender

        Returns:
            ResolutionResult recording that defend was used.
        """
        return ResolutionResult(
            action_name="defend",
            attacker_id=defender_id,
            target_id=defender_id,
            raw_roll=0,
            modified_damage=0,
            healing_done=0,
            target_hp_before=defender_hp,
            target_hp_after=defender_hp,
            is_kill=False,
        )
