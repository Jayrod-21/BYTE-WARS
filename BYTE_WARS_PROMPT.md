# BYTE Wars — Claude Code Master Prompt

> **Usage:** Use this prompt to initialize a new Claude Code overnight session.
> Prepend with the contents of `BYTE_WARS_CONTEXT.md` for full project context.
> Update the PHASE INSTRUCTIONS section for each new phase.

---

## Master Prompt

```
You are working on BYTE Wars — a mobile-first AI battle arena where AI champions
fight in free-for-all pixel art matches with Solana-based wagering and NFT gear.

Read BYTE_WARS_CONTEXT.md first. Follow all core rules defined there.
Do not break the rules listed under "Core Rules (Do Not Break These)."

Default language: Python.
Include docstrings and inline comments explaining what each section does —
the owner is learning to code.

Target environment: Docker. All services must be runnable via docker-compose up.

Do not skip error handling. Every API call, DB query, and external service
interaction must have try/except with meaningful error messages.

After completing each task:
- Add a comment block at the top of the file summarizing what it does
- Update any relevant data structures if the implementation revealed a gap
- Do not move to the next task until the current one passes a basic smoke test
```

---

## Phase Prompt Swap Guide

When moving to a new phase, replace the PHASE INSTRUCTIONS section with
the corresponding phase from BYTE_WARS_TASKLIST.md. Always keep the master
instructions above the phase block — they apply to every session.

---

## Quick Phase Reference

| Phase | Prompt Focus |
|---|---|
| 1 | Battle engine core, mock bots, Docker setup |
| 2 | MCP tool server, real action calls |
| 3 | Champion builder API, system prompt storage |
| 4 | Match orchestration, lobby, 1v1v1v1 |
| 5 | Playback renderer, battle history → animation data |
| 6 | Web/frontend interface |
| 7 | Solana wallet connection, NFT stub |
| 8 | Wagering smart contract + escrow |
| 9 | NFT marketplace |
| 10 | Mobile optimization |
| 11 | Production hardening + deployment |
