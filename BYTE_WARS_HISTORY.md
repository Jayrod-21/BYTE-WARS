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

## [2026-03-19] — Phase 2: MCP Tool Action System

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] FastMCP server with all 5 base actions registered as callable MCP tools
- [x] ToolRegistry: central registry with dynamic tool registration/unregistration
- [x] ToolBridge: connects MCP tool calls to DamageResolver for resolution
- [x] GameState: builds complete game state for bots each turn (own stats, opponents, tools, history)
- [x] GameState.to_prompt(): converts game state to human-readable prompt for AI models
- [x] BotResponseParser: validates bot responses, catches errors, auto-corrects targets, provides fallback
- [x] Dynamic NFT skill registration and resolution verified in battle
- [x] Battle engine refactored to use MCP pipeline (ToolBridge + BotResponseParser)
- [x] 7 integration tests all passing (registry, bridge, game state, parser, server, full battle, dynamic tools)
- [x] Phase 1 tests still pass (backward compatible)

**Decisions Made:**
- Renamed local `mcp/` package to `mcp_tools/` to avoid shadowing the installed MCP SDK
- BotResponseParser accepts both JSON strings and Python lists (flexible for AI responses)
- Invalid bot responses fall back to basic_strike on a random opponent (match never crashes)
- GameState includes last 3 turns of history for tactical context
- Tool schemas are simplified versions of full action defs (only fields bots need)

**Open Issues / Blockers:**
- None

**Next Step:**
- Phase 3: Champion Builder — CRUD API for champions with system prompt and gear management

---

## [2026-03-19] — Phase 4: Match Orchestration

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] AIBot class: real AI API integration for Claude, GPT, Gemini (OpenAI-compatible)
- [x] Match service: lobby creation, state machine (pending → active → complete | timed_out)
- [x] Match API routes: POST /matches, POST /matches/{id}/start, GET /matches/{id}, GET /matches
- [x] Per-champion bot selection: AIBot for champions with API keys, MockBot fallback
- [x] Bot response timeout: 12s async timeout, falls back to random actions
- [x] Multi-bot free-for-all: tested 1v1, 1v1v1, and 1v1v1v1 matches
- [x] Winner determination and full turn history storage
- [x] Match data never leaks encrypted API keys
- [x] 11 test groups all passing, all prior phases still green

**Decisions Made:**
- Battle execution is inline-awaited (not background task) for reliability
- AI API calls use httpx async client with 10s timeout per call
- Anthropic uses Messages API format; all others use OpenAI chat completions
- JSON extraction from AI responses handles markdown code blocks and raw text
- UUID type mismatch fixed between champion service (UUID) and battle engine (str)

**Next Step:**
- Phase 5: Playback & Visualization System

---

## [2026-03-19] — Phase 3: Champion Builder

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] Archetype system: 5 archetypes (tank, assassin, mage, ranger, support) with default stats and base gear
- [x] Champion creation API (POST /api/champions) with archetype-based defaults
- [x] Champion retrieval (GET /api/champions/{id}) and listing (GET /api/champions)
- [x] Champion update (PATCH /api/champions/{id}) with rule enforcement
- [x] Pydantic schemas with validation (slot limits, archetype check, name length)
- [x] API key encryption at rest using Fernet symmetric encryption
- [x] API keys never returned in responses (has_api_key boolean instead)
- [x] Base gear immutability enforced (core rule #3)
- [x] Cross-archetype gear selection allowed
- [x] AI model selection stored per champion
- [x] 12 test groups all passing

**Decisions Made:**
- In-memory champion storage for Phase 3 (PostgreSQL queries added in Phase 4)
- Fernet encryption for API keys with env-based key (ENCRYPTION_KEY)
- Routes mounted at /api/champions prefix
- Archetype cannot be changed after creation
- Stats determined by archetype (no direct stat modification)

**Next Step:**
- Phase 4: Match Orchestration — lobby system, real AI model integration

---

<!-- Add new entries above this line as phases complete -->
