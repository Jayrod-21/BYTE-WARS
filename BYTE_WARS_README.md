# BYTE Wars — AI Champion Coliseum

> *"Sponsor your gladiator. Watch it fight. Win or lose everything."*

---

## What Is BYTE Wars?

BYTE Wars is a mobile-first AI battle arena where users build AI champions — custom-prompted bots equipped with gear and skills — and pit them against each other in turn-based, free-for-all combat. Battles are resolved by the engine, then rendered as a pixel art playback for spectators. Users wager on outcomes using Solana before matches begin.

This is AI entertainment infrastructure: platform-agnostic, spectator-friendly, and built around real AI models (Claude, Gemini, GPT, etc.) fighting each other through an MCP tool layer.

---

## Quick Start (Docker)

```bash
# Clone and build
git clone <repo>
cd BYTE-WARS
docker compose up --build

# Services:
# - battle-engine (Python/FastAPI) :8000
# - postgres :5432
# - redis :6379
```

## Run Battle Tests (No Docker Required)

```bash
cd backend
pip install -r requirements.txt
python tests/test_battle.py
```

---

## Project Structure

```
BYTE-WARS/
├── BYTE_WARS_README.md          # This file
├── BYTE_WARS_CONTEXT.md         # Session primer for Claude
├── BYTE_WARS_PROMPT.md          # Master Claude Code prompt
├── BYTE_WARS_TASKLIST.md        # Full phased task list
├── BYTE_WARS_HISTORY.md         # Session-by-session decision log
├── docker-compose.yml
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── database.py              # Async SQLAlchemy setup
│   ├── engine/                  # Battle engine modules
│   │   ├── actions.py           # 5 base MCP combat actions
│   │   ├── battle_engine.py     # Main battle loop
│   │   ├── damage_resolver.py   # Probabilistic damage calculation
│   │   ├── turn_manager.py      # Pathfinder 2e action economy
│   │   └── mock_bot.py          # Random action bot for testing
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── champion.py          # Champion data model
│   │   └── match.py             # Match data model
│   ├── mcp/                     # MCP tool server (Phase 2)
│   ├── services/                # External services (Phase 7+)
│   └── tests/
│       └── test_battle.py       # Battle engine validation script
├── frontend/                    # React Native / Expo (Phase 6)
└── contracts/                   # Solana programs (Phase 8)
```

---

## Current Phase: Phase 1 — Battle Engine Core (Complete)

See `BYTE_WARS_TASKLIST.md` for the full phased build plan.
