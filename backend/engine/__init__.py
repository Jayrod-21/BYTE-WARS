"""
engine/ — BYTE Wars Battle Engine modules.

Contains the core battle logic:
- actions: Base MCP tool set (5 combat actions)
- damage_resolver: Probabilistic damage calculation with stat modifiers
- turn_manager: Pathfinder 2e action economy (3 actions per turn)
- battle_engine: Main battle loop that runs a full match
"""

from engine.actions import ACTIONS, get_action
from engine.damage_resolver import DamageResolver
from engine.turn_manager import TurnManager
from engine.battle_engine import BattleEngine

__all__ = ["ACTIONS", "get_action", "DamageResolver", "TurnManager", "BattleEngine"]
