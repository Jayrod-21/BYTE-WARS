# BYTE Wars — Project History Log

> This file tracks key decisions, phase completions, pivots, and lessons learned.
> Update this file at the end of every Claude Code session or significant work block.

---

## [2025-03-19] — Project Inception & Ideation

**Status:** Complete
**Session Model:** claude-sonnet-4-6 (planning/ideation)

**Origin:**
- Concept emerged from a brainstorming session exploring AI entertainment and monetization
- Core idea: AI models (Claude, Gemini, GPT, etc.) fight each other in a turn-based arena
- Inspired by Coliseum gladiator sponsorship model + Hunger Games dynamic
- Working title established: **BYTE Wars**

**Decisions Made:**
- Battle format: Free-for-all (1v1, 1v1v1, 1v1v1v1) — NO teams
- Turn economy: Pathfinder 2nd Edition action point system (3 actions per turn)
- Damage: Probabilistic ranges, not fixed values
- Starting gear: Cannot be lost — floor protection for all champions
- Gear/skill slots: Limited, enforcing strategic tradeoffs
- Cross-archetype gear selection: Allowed
- Champion identity: Custom system prompt (owner-written) + premade archetype loadout
- AI models: Platform-agnostic — users bring their own API keys
- Blockchain: Solana (Metaplex for NFTs)
- Wagering: Pre-match only, platform takes cut
- Visualization: Pixel art, playback after battle resolution (not real-time)
- Primary interface: Mobile-first (PWA or React Native)
- Build approach: Phased, Docker first

**Next Step:**
- Begin Phase 1: Battle Engine Core

---

## [2026-03-19] — Phase 1: Battle Engine Core

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] Docker Compose setup (FastAPI + PostgreSQL + Redis) with health checks
- [x] FastAPI app with /health endpoint (reports API, DB, Redis status)
- [x] Champion SQLAlchemy model (UUID, owner, name, archetype, stats, gear/skill slots, base gear, API key, model)
- [x] Match SQLAlchemy model (status lifecycle, champion IDs, turn history JSON, winner, timestamps)
- [x] Turn Manager with Pathfinder 2e action economy (3 AP/turn, initiative = endurance + d20)
- [x] Damage Resolver with probabilistic rolls, strength modifier, endurance defense, defend buff
- [x] 5 base MCP actions defined (basic_strike, heavy_blow, defend, power_surge, heal)
- [x] Battle Engine loop: 2-4 champions, 50-turn limit, mock bot random selection
- [x] Complete BattleHistory logging (every action, roll, damage, HP change)
- [x] Test script: 10 battles validated successfully

**Decisions Made:**
- Graceful startup when DB unavailable (for local dev without Docker)
- Damage minimum set to 1.0 (no zero-damage hits)
- Healing modified by endurance stat (endurance / 200 bonus)
- Initiative ties broken by random shuffle before stable sort

**Balance Validation (50 battles):**
- 0 timeouts (0% < 20% threshold) ✅
- 0 battles under 3 turns (min: 5) ✅
- Average 9.4 turns per match
- Tank archetype favored with random bots (expected — intentional strategy will balance this)

**Open Issues / Blockers:**
- Tank archetype wins ~70% with random bots — will self-correct when real AI strategies are plugged in (Phase 4)
- Docker daemon not available in cloud dev environment — Docker Compose config validated via parsing only

**Next Step:**
- Phase 2: MCP Tool Action System — register base actions as real MCP tools

---

<!-- Add new entries above this line as phases complete -->
