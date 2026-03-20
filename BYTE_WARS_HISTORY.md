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

## [2026-03-20] — Phase 10: Mobile Optimization (PWA)

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] Decision: PWA (not React Native) — existing React+Vite app, no native features needed
- [x] PWA manifest: standalone display, portrait, theme #0a0a1a, 192/512 icons
- [x] Service worker: app shell caching, playback/match API cache (network-first), push notifications
- [x] App icons: pixel art BW icon in SVG favicon + 192px + 512px PNG
- [x] HTML meta tags: theme-color, viewport-fit=cover, apple-mobile-web-app-capable, no-zoom
- [x] Mobile CSS: 44px min touch targets, 16px inputs (prevent iOS zoom), safe-area insets
- [x] Nav: horizontal scroll on mobile, condensed link sizing
- [x] Pixel art: image-rendering: pixelated/crisp-edges for SVG sprites
- [x] GPU acceleration: will-change + translateZ(0) for animated elements
- [x] Notification service: requestPermission, notifyMatchComplete, notifyWagerResult
- [x] Match lobby triggers notification on match completion
- [x] Service worker registered in main.jsx on load
- [x] 10 test groups passing, all prior phases green

**Decisions Made:**
- PWA over React Native: game is turn-based, no camera/GPS/native APIs needed
- Service worker caches playback + match data for offline re-watching
- No-zoom viewport (max-scale=1, user-scalable=no) for app-like feel
- 44px minimum touch targets per WCAG/Apple HIG guidelines
- Safe-area-inset-* for notched devices (iPhone X+)
- Push notifications are local-only for now; real push server in Phase 11

**Next Step:**
- Phase 11: Production Hardening & Deployment

---

## [2026-03-20] — Phase 9: NFT Marketplace

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] Loot table system: drop rates per rarity (common 50%, uncommon 30%, rare 15%, legendary 5%)
- [x] Loot chest generation: 3 items per chest, 70% gear / 30% skill mix
- [x] Loot chest awarded on match win: integrated into match_service._execute_battle()
- [x] Loot chest display: PlaybackPage shows chest items, InventoryPage has Chests tab
- [x] NFT transfer: transfer_nft() moves ownership between users with inventory update
- [x] Marketplace listing: create_listing() with ownership check and duplicate prevention
- [x] Marketplace cancellation: cancel_listing() with seller verification
- [x] Marketplace purchase: purchase_listing() with SOL payment, NFT transfer, seller credit
- [x] Marketplace browse: browse_listings() with type/rarity/archetype filters
- [x] NFT detail page: get_nft_detail() with listing history and marketplace status
- [x] Frontend MarketplacePage: browse with filters, buy button, price display
- [x] Frontend InventoryPage: "Sell on Marketplace" button, loot chests tab
- [x] API client: 7 new marketplace/transfer endpoint functions
- [x] Match response includes loot_chest_id and loot_chest_items
- [x] 12 test groups all passing, all prior phases green

**Decisions Made:**
- Loot chest = 3 items (keeps rewards meaningful but not overwhelming)
- 70/30 gear-to-skill ratio in chests (gear is more generally useful)
- Marketplace uses simulated SOL (same wallet system as Phase 8 wagers)
- Marketplace purchase credits seller's wallet directly (platform fee on wagers only, not marketplace — can add later)
- Cannot list an NFT that's already actively listed (prevents confusion)
- Cannot buy your own listing (prevents wash trading)
- NFT detail includes full listing history for provenance
- Loot chest items are immediately added to inventory (no "unopened" state in Phase 9 — animation is cosmetic)

**Next Step:**
- Phase 10: Mobile Optimization (PWA vs React Native decision)

---

## [2026-03-20] — Phase 8: Wagering System

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] Wager data model: Wager, EscrowAccount, WalletBalance dataclasses with full lifecycle states
- [x] Simulated Solana devnet: stub tx hashes, PDA escrow addresses, wallet balances (100 SOL start)
- [x] WagerService: place_wager(), cancel_wager(), lock_escrow(), distribute_payouts(), refund_all()
- [x] Platform fee: 5% deduction from total pot before payout
- [x] Proportional payout: winners split net pot proportional to their wager amounts
- [x] Refund logic: full refund on timed-out/cancelled matches or when nobody bets on the winner
- [x] Odds calculation: per-champion totals and implied payout multiplier
- [x] Wager API routes: place, cancel, match wagers, user history, odds, escrow info, wallet balance, airdrop
- [x] Match service integration: escrow locked on match start, payouts/refunds on match completion
- [x] Frontend MatchLobbyPage: optional wager section with champion selector, amount input, odds display
- [x] Frontend PlaybackPage: wager results section showing won/lost/refunded with SOL amounts
- [x] Frontend WagerHistoryPage: P&L summary, wager list with match links
- [x] API client: 7 new wager endpoint functions
- [x] 12 test groups all passing, all prior phases green

**Decisions Made:**
- Simulated Solana (stub) — same pattern as Phase 7 NFTs; real Anchor contract in Phase 11
- Wallets start with 100 SOL on devnet; airdrop endpoint for testing
- One wager per user per match (prevents self-arbitrage)
- Wagers can be cancelled before match starts (placed → cancelled)
- Platform fee = 5% of total pot, applied at escrow lock time
- If nobody bet on the winner, all wagers are refunded (prevents unfair loss)
- MIN_WAGER = 0.01 SOL, MAX_WAGER = 100 SOL
- Wager history sorted newest-first

**Security Audit Checklist (for production Anchor contract):**
- [ ] Escrow PDA derived correctly (no seed collision)
- [ ] Only match creator can initialize escrow
- [ ] Wager placement verifies signer owns the wallet
- [ ] Escrow lock is atomic with match start
- [ ] Payout instruction validates winner from match result
- [ ] Refund instruction validates match timed_out status
- [ ] Platform fee account is hardcoded (not user-supplied)
- [ ] Re-entrancy protection on all fund transfers
- [ ] Integer overflow protection on SOL arithmetic
- [ ] Rate limiting on wager placement
- [ ] Double-spend prevention (check tx uniqueness)

**Next Step:**
- Phase 9: NFT Marketplace (real minting, loot chests, marketplace)

---

## [2026-03-20] — Phase 7: Solana Wallet + NFT Stub Integration

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] NFT data model: NFTItem dataclass with type, rarity, archetype affinity, stat bonuses, skill actions
- [x] Gear catalog: 17 items across 4 rarities (common, uncommon, rare, legendary)
- [x] Skill catalog: 8 NFT skills with action definitions (fireball, shadow_step, etc.)
- [x] Rarity multiplier system (common 1.0x → legendary 3.0x)
- [x] Archetype affinity: 25% stat bonus when NFT matches champion archetype
- [x] Starter inventory generation: 4 gear + 2 skills per owner
- [x] NFT minting from catalog with ownership tracking
- [x] Equip gear to champion gear slots (max 6) with ownership verification
- [x] Equip skills to champion skill slots (max 4) with ownership verification
- [x] NFT gear stat bonuses applied in battle engine via NFTService.apply_gear_bonuses()
- [x] NFT skills registered as MCP tools dynamically per battle (fresh ToolRegistry)
- [x] Wallet link endpoint (POST /nft/wallet/link) ties Solana address to user account
- [x] NFT inventory API: catalog browse, inventory list, generate, mint, equip
- [x] Frontend InventoryPage with gear/skill filter and rarity-colored cards
- [x] 12 test groups all passing, all prior phases green

**Decisions Made:**
- In-memory NFT storage (consistent with other services, PostgreSQL later)
- Fresh ToolRegistry per battle to prevent skill tool leakage between matches
- Starter inventory is idempotent (re-generate returns existing items)
- NFT ownership verified on equip (cannot equip another owner's NFT)
- Gear and skill catalogs are static dicts for stub phase; will become on-chain metadata in Phase 9

**Next Step:**
- Phase 8: Wagering System (Solana devnet, escrow smart contract, wager placement)

---

## [2026-03-20] — Phase 6: Web Interface

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] JWT auth: registration, login, token validation, protected /auth/me endpoint
- [x] React frontend (Vite): 7 pages with React Router
- [x] Login/Register page with toggle and error handling
- [x] Champion list page with archetype filtering
- [x] Champion builder page with archetype selector, system prompt, AI model, API key
- [x] Match lobby page: select 2-4 champions, fight button with auto-navigation
- [x] Playback viewer page: embedded HTML viewer with stats toggle
- [x] Match history page: sorted by date, status badges, watch playback links
- [x] Profile page with authenticated user info
- [x] Mobile-first responsive CSS (dark theme, monospace font)
- [x] API client with token management and proxy config
- [x] 8 test groups all passing, all prior phases green

**Decisions Made:**
- Vite + React (not Expo) for Phase 6 — web-first, Expo for mobile in later phase
- JWT with bcrypt password hashing, 24h token expiration
- Dark cyberpunk theme matching the playback viewer aesthetic
- Vite proxy to backend during dev (`/api` → `localhost:8000`)
- Frontend builds to `frontend/dist/` (252KB gzipped)

**Next Step:**
- Phase 7: NFT Gear & Skills (Solana/Metaplex)

---

## [2026-03-20] — Phase 5: Playback & Visualization System

**Status:** Complete
**Session Model:** claude-opus-4-6

**Work Done:**
- [x] PlaybackEvent system: 10 event types with timing metadata
- [x] BattleHistory → PlaybackData converter with match summary stats
- [x] Pixel art SVG sprite system: 16x16 pixel grids for all 5 archetypes
- [x] Self-contained HTML playback viewer with CSS animations
- [x] Arena renderer with HP bars, damage popups, action log
- [x] Speed controls (0.5x, 1x, 2x, skip), pause/play, restart
- [x] Match summary overlay with per-champion stats
- [x] Playback + Sprite API endpoints with shareable links
- [x] 10 test groups all passing, all prior phases green

**Decisions Made:**
- SVG sprites (inline pixel grids) — no raster assets needed, perfect scaling
- Self-contained HTML viewer — no external dependencies, works standalone
- Events timestamped in ms with duration for smooth animation scheduling

**Next Step:**
- Phase 6: Web Interface

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
