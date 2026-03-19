# BYTE Wars — Project Context & Session Primer

> **Purpose:** Paste this file (or reference it) at the start of every new Claude Code session.
> It gives the AI full context on what BYTE Wars is, what's been built, and what the rules are.

---

## TL;DR for Claude

You are working on **BYTE Wars**, a mobile-first AI battle arena where:
- Users build AI champions (custom system prompt + gear loadout)
- Champions fight in free-for-all matches (1v1 to 1v1v1v1)
- The battle engine resolves the full match, then a pixel art playback is rendered
- Users wager on outcomes pre-match using Solana
- Gear and skills are NFTs on Solana (Metaplex)
- AI models are platform-agnostic — users bring their own API keys (Claude, Gemini, GPT)
- MCP tools = the available actions a bot can take each turn

**Default language: Python. Include JSDoc-style docstrings and inline comments.**
**Docker is the deployment target until production is ready.**

---

## Core Rules (Do Not Break These)

1. **Turn economy = Pathfinder 2nd Edition** — 3 action points per turn. Each MCP tool call costs 1-3 actions depending on the skill.
2. **Damage is probabilistic** — actions have min/max damage ranges. Always use RNG resolution.
3. **Starting gear is permanent** — a champion can never lose their base loadout. This is the floor.
4. **No teams** — all multi-bot matches are free-for-all. Last bot with HP wins.
5. **Time limit enforced** — if no winner by time limit, all remaining bots lose.
6. **Battles resolve fully before visualization** — the engine runs the whole match, logs the history, then playback renders it. Not real-time.
7. **Platform-agnostic AI** — the battle engine must support any OpenAI-compatible API endpoint. Users supply their own keys.

---

## Champion Structure

```python
champion = {
    "id": "uuid",
    "owner_wallet": "solana_address",
    "owner_user_id": "uuid",
    "name": "string",
    "system_prompt": "string (custom strategy/personality)",
    "archetype": "tank | assassin | mage | ranger | support",
    "stats": {
        "health": int,          # base HP pool
        "strength": int,        # damage modifier
        "endurance": int,       # action economy modifier / durability
    },
    "gear_slots": [],           # max 6 slots (NFT items)
    "skill_slots": [],          # max 4 slots (NFT skills)
    "base_gear": [],            # PERMANENT — cannot be removed or lost
    "api_key": "encrypted",     # owner's AI provider API key
    "model": "claude-sonnet-4-6 | gemini-pro | gpt-4o | etc."
}
```

---

## Battle Engine Flow

```
1. Match created → bots registered → wagers locked on Solana
2. Turn order determined (initiative roll: endurance + d20)
3. For each turn:
   a. Bot receives: current game state, own stats, opponent stats, available MCP tools
   b. Bot responds with: chosen actions (up to 3 action points worth)
   c. Engine resolves: damage calculated with RNG, stats updated
   d. History entry logged
4. Match ends: last bot standing, or turn limit (50) hit
5. Payouts triggered on Solana smart contract
6. Loot chests distributed to winner(s)
7. Battle history passed to playback renderer
```

---

## MCP Tool Structure (Actions)

Each action is an MCP tool. Tools have:
- `action_point_cost`: 1, 2, or 3
- `damage_range`: [min, max] or null (for utility skills)
- `stat_requirement`: which stat affects this tool's effectiveness
- `target`: self | single_enemy | all_enemies | aoe

Current base actions:
```
basic_strike       — cost 1, damage [5, 12], requires strength
heavy_blow         — cost 2, damage [15, 25], requires strength
defend             — cost 1, damage null, reduces incoming damage by 30%
power_surge        — cost 3, damage [30, 50], requires strength + endurance
heal               — cost 2, restores [10, 20] HP, requires endurance
```

---

## Tech Stack Reference

| Layer | Tech | Notes |
|---|---|---|
| Battle Engine | Python + FastAPI | Core logic lives here |
| MCP Server | Python MCP SDK | Actions as tools |
| Frontend | React Native / Expo | Mobile-first |
| Blockchain | Solana + Metaplex | NFTs + wagering |
| Wallet | Phantom adapter | Primary wallet |
| DB | PostgreSQL | Match history, accounts |
| Cache | Redis | Active match state |
| Container | Docker Compose | Dev + staging |

---

## Current Phase

**Current Phase:** Phase 2 — MCP Tool Action System (Complete)
**Last Completed:** Phase 2 (2026-03-19)
**Next Task:** Phase 3 — Champion Builder
**Blocked On:** Nothing currently.
