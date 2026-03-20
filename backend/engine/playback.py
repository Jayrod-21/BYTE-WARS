"""
engine/playback.py — Battle History to Playback Event converter for BYTE Wars.

Converts raw BattleHistory turn data into a structured sequence of PlaybackEvents
that the frontend animation system can render frame-by-frame.

Event types:
- match_start: Match begins, champion introductions
- turn_start: New turn begins for a champion
- attack: Champion attacks a target
- defend: Champion enters defensive stance
- heal: Champion heals themselves
- damage_taken: Target takes damage (separate from attack for animation timing)
- death: Champion is eliminated
- turn_end: Champion's turn ends
- match_end: Match concludes with winner/timeout

Each event carries timing metadata for the animation sequencer.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum


class EventType(str, Enum):
    """All possible playback event types."""
    MATCH_START = "match_start"
    TURN_START = "turn_start"
    ATTACK = "attack"
    DEFEND = "defend"
    SKILL_USE = "skill_use"
    DAMAGE_TAKEN = "damage_taken"
    HEAL = "heal"
    DEATH = "death"
    TURN_END = "turn_end"
    MATCH_END = "match_end"


@dataclass
class PlaybackEvent:
    """
    A single animation event in the playback sequence.

    Each event maps to a visual animation in the renderer:
    - type: What kind of event (attack, heal, death, etc.)
    - timestamp: Relative time in the playback sequence (ms)
    - duration: How long this animation should take (ms)
    - champion_id: Who is performing the action
    - target_id: Who is being affected (if applicable)
    - data: Event-specific payload (damage, HP values, action name, etc.)
    """
    type: str
    timestamp: int  # ms from playback start
    duration: int   # ms for this animation
    champion_id: str
    champion_name: str = ""
    target_id: str | None = None
    target_name: str | None = None
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlaybackData:
    """
    Complete playback package for a match.

    Contains everything the renderer needs:
    - Match metadata (participants, winner, duration)
    - Ordered list of PlaybackEvents for animation
    - Champion info for sprite/stat bar rendering
    - Match summary stats (damage dealt, heals, kills)
    """
    match_id: str
    events: list[dict]
    champions: list[dict]  # id, name, archetype, max_hp
    winner_id: str | None
    winner_name: str | None
    status: str
    total_turns: int
    summary: dict  # Per-champion stats

    def to_dict(self) -> dict:
        return asdict(self)


# Base animation durations (ms) — scaled by playback speed
TIMING = {
    "match_start": 2000,
    "turn_start": 400,
    "attack": 600,
    "defend": 400,
    "skill_use": 800,
    "damage_taken": 500,
    "heal": 600,
    "death": 1200,
    "turn_end": 200,
    "match_end": 3000,
}


def convert_history_to_playback(
    match_data: dict,
) -> PlaybackData:
    """
    Convert a completed match's data into a PlaybackData object.

    Takes the raw match data (with turn_history from the battle engine)
    and produces an ordered sequence of PlaybackEvents suitable for
    frame-by-frame animation rendering.

    Args:
        match_data: Complete match data dict from the match service.
                   Must include turn_history, champion_ids, champion_names, etc.

    Returns:
        PlaybackData with ordered events and match summary.
    """
    events: list[dict] = []
    timestamp = 0  # Running timestamp in ms

    champion_ids = match_data.get("champion_ids", [])
    champion_names = match_data.get("champion_names", [])
    turn_history = match_data.get("turn_history", [])

    # Build champion lookup for names
    name_lookup = {}
    for i, cid in enumerate(champion_ids):
        name_lookup[cid] = champion_names[i] if i < len(champion_names) else f"Champion {i+1}"

    # Build champion info for renderer
    champion_data = match_data.get("champion_data", [])
    champions_info = []
    for i, cid in enumerate(champion_ids):
        info = {"id": cid, "name": name_lookup.get(cid, "")}
        if i < len(champion_data):
            cd = champion_data[i]
            info["archetype"] = cd.get("archetype", "ranger")
            info["max_hp"] = cd.get("stats", {}).get("health", 100)
            info["stats"] = cd.get("stats", {})
        else:
            info["archetype"] = "ranger"
            info["max_hp"] = 100
            info["stats"] = {}
        champions_info.append(info)

    # --- Match Start Event ---
    events.append(PlaybackEvent(
        type=EventType.MATCH_START,
        timestamp=timestamp,
        duration=TIMING["match_start"],
        champion_id="system",
        champion_name="System",
        data={
            "champion_count": len(champion_ids),
            "champion_names": list(champion_names),
        },
    ).to_dict())
    timestamp += TIMING["match_start"]

    # --- Track stats for summary ---
    summary_stats = {}
    for cid in champion_ids:
        summary_stats[cid] = {
            "name": name_lookup.get(cid, ""),
            "damage_dealt": 0,
            "damage_taken": 0,
            "healing_done": 0,
            "kills": 0,
            "actions_taken": 0,
            "turns_survived": 0,
            "used_fallback_count": 0,
        }

    # --- Track current HP for stat bars ---
    current_hp = {}
    for info in champions_info:
        current_hp[info["id"]] = info.get("max_hp", 100)

    # --- Process each turn ---
    current_turn_number = 0

    for turn_entry in turn_history:
        turn_number = turn_entry.get("turn_number", 0)
        champion_id = turn_entry.get("champion_id", "")
        champion_name = turn_entry.get("champion_name", "")
        actions_taken = turn_entry.get("actions_taken", [])
        resolutions = turn_entry.get("resolutions", [])
        used_fallback = turn_entry.get("used_fallback", False)

        # Update summary
        if champion_id in summary_stats:
            summary_stats[champion_id]["turns_survived"] = turn_number
            summary_stats[champion_id]["actions_taken"] += len(actions_taken)
            if used_fallback:
                summary_stats[champion_id]["used_fallback_count"] += 1

        # Turn start event (only emit once per turn number)
        if turn_number != current_turn_number:
            current_turn_number = turn_number

        events.append(PlaybackEvent(
            type=EventType.TURN_START,
            timestamp=timestamp,
            duration=TIMING["turn_start"],
            champion_id=champion_id,
            champion_name=champion_name,
            data={
                "turn_number": turn_number,
                "used_fallback": used_fallback,
            },
        ).to_dict())
        timestamp += TIMING["turn_start"]

        # Process each action + its resolution
        for i, action in enumerate(actions_taken):
            action_name = action.get("action", "unknown")
            target_id = action.get("target_id", "")
            target_name = name_lookup.get(target_id, "")

            # Find matching resolution
            resolution = resolutions[i] if i < len(resolutions) else None

            # Determine event type based on action
            if action_name == "defend":
                events.append(PlaybackEvent(
                    type=EventType.DEFEND,
                    timestamp=timestamp,
                    duration=TIMING["defend"],
                    champion_id=champion_id,
                    champion_name=champion_name,
                    data={"action": action_name},
                ).to_dict())
                timestamp += TIMING["defend"]

            elif action_name == "heal":
                heal_amount = 0
                hp_after = current_hp.get(champion_id, 0)
                if resolution:
                    heal_amount = resolution.get("healing_done", 0)
                    hp_after = resolution.get("target_hp_after", hp_after)
                    current_hp[champion_id] = hp_after
                    if champion_id in summary_stats:
                        summary_stats[champion_id]["healing_done"] += heal_amount

                events.append(PlaybackEvent(
                    type=EventType.HEAL,
                    timestamp=timestamp,
                    duration=TIMING["heal"],
                    champion_id=champion_id,
                    champion_name=champion_name,
                    data={
                        "action": action_name,
                        "heal_amount": heal_amount,
                        "hp_after": hp_after,
                    },
                ).to_dict())
                timestamp += TIMING["heal"]

            else:
                # Attack action
                damage = 0
                hp_before = current_hp.get(target_id, 0)
                hp_after = hp_before
                is_kill = False

                if resolution:
                    damage = resolution.get("modified_damage", 0)
                    hp_before = resolution.get("target_hp_before", hp_before)
                    hp_after = resolution.get("target_hp_after", hp_after)
                    is_kill = resolution.get("is_kill", False)
                    current_hp[target_id] = hp_after

                    if champion_id in summary_stats:
                        summary_stats[champion_id]["damage_dealt"] += damage
                    if target_id in summary_stats:
                        summary_stats[target_id]["damage_taken"] += damage

                # Attack event
                events.append(PlaybackEvent(
                    type=EventType.ATTACK,
                    timestamp=timestamp,
                    duration=TIMING["attack"],
                    champion_id=champion_id,
                    champion_name=champion_name,
                    target_id=target_id,
                    target_name=target_name,
                    data={
                        "action": action_name,
                        "damage": damage,
                        "cost": action.get("cost", 1),
                    },
                ).to_dict())
                timestamp += TIMING["attack"]

                # Damage taken event (separate for animation stagger)
                events.append(PlaybackEvent(
                    type=EventType.DAMAGE_TAKEN,
                    timestamp=timestamp,
                    duration=TIMING["damage_taken"],
                    champion_id=target_id,
                    champion_name=target_name,
                    target_id=champion_id,
                    target_name=champion_name,
                    data={
                        "damage": damage,
                        "hp_before": hp_before,
                        "hp_after": hp_after,
                    },
                ).to_dict())
                timestamp += TIMING["damage_taken"]

                # Death event
                if is_kill:
                    if champion_id in summary_stats:
                        summary_stats[champion_id]["kills"] += 1

                    events.append(PlaybackEvent(
                        type=EventType.DEATH,
                        timestamp=timestamp,
                        duration=TIMING["death"],
                        champion_id=target_id,
                        champion_name=target_name,
                        data={
                            "killed_by": champion_id,
                            "killed_by_name": champion_name,
                            "final_action": action_name,
                        },
                    ).to_dict())
                    timestamp += TIMING["death"]

        # Turn end
        events.append(PlaybackEvent(
            type=EventType.TURN_END,
            timestamp=timestamp,
            duration=TIMING["turn_end"],
            champion_id=champion_id,
            champion_name=champion_name,
            data={"turn_number": turn_number},
        ).to_dict())
        timestamp += TIMING["turn_end"]

    # --- Match End Event ---
    events.append(PlaybackEvent(
        type=EventType.MATCH_END,
        timestamp=timestamp,
        duration=TIMING["match_end"],
        champion_id=match_data.get("winner_id", "") or "system",
        champion_name=match_data.get("winner_name", "") or "No Winner",
        data={
            "status": match_data.get("status", "unknown"),
            "winner_id": match_data.get("winner_id"),
            "winner_name": match_data.get("winner_name"),
            "total_turns": match_data.get("total_turns", 0),
            "total_duration_ms": timestamp + TIMING["match_end"],
        },
    ).to_dict())

    return PlaybackData(
        match_id=match_data.get("id", ""),
        events=events,
        champions=champions_info,
        winner_id=match_data.get("winner_id"),
        winner_name=match_data.get("winner_name"),
        status=match_data.get("status", "unknown"),
        total_turns=match_data.get("total_turns", 0),
        summary=summary_stats,
    )
