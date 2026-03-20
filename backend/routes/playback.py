"""
routes/playback.py — Playback & Visualization API for BYTE Wars.

Provides endpoints for match playback:
- GET /playback/{match_id}       — Get playback event data (JSON)
- GET /playback/{match_id}/watch — Render the HTML playback viewer
- GET /playback/{match_id}/share — Get a shareable playback link
- GET /sprites/{archetype}       — Get SVG sprite for an archetype

The playback viewer is a self-contained HTML page with:
- Canvas-based arena renderer
- SVG pixel art sprites per archetype
- HP bar overlays
- Turn-by-turn animation sequencer
- Speed controls (0.5x, 1x, 2x, skip)
- Match summary screen at the end
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from engine.playback import convert_history_to_playback
from engine.sprites import get_sprite_svg, get_all_sprites, SPRITE_GRIDS
from services.match_service import MatchService


router = APIRouter(prefix="/playback", tags=["Playback"])
_match_service = MatchService()


@router.get("/{match_id}")
async def get_playback_data(match_id: str) -> dict:
    """
    Get structured playback event data for a match.

    Returns the full PlaybackData JSON including events, champions,
    summary stats, and timing information.

    The frontend can use this to drive its own custom renderer,
    or use the built-in /watch endpoint for the default viewer.
    """
    match_data = _match_service.get_match(match_id)
    if match_data is None:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    if match_data.get("status") not in ("complete", "timed_out"):
        raise HTTPException(
            status_code=400,
            detail=f"Match is still '{match_data.get('status')}'. Wait for completion.",
        )

    playback = convert_history_to_playback(match_data)
    return playback.to_dict()


@router.get("/{match_id}/watch", response_class=HTMLResponse)
async def watch_playback(match_id: str) -> str:
    """
    Render the built-in HTML playback viewer for a match.

    Returns a self-contained HTML page with the full animation
    sequencer, sprites, HP bars, and speed controls.
    """
    match_data = _match_service.get_match(match_id)
    if match_data is None:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    if match_data.get("status") not in ("complete", "timed_out"):
        raise HTTPException(
            status_code=400,
            detail=f"Match is still '{match_data.get('status')}'. Wait for completion.",
        )

    playback = convert_history_to_playback(match_data)
    sprites = get_all_sprites(scale=4)

    import json
    playback_json = json.dumps(playback.to_dict())
    sprites_json = json.dumps(sprites)

    html = _build_playback_html(playback_json, sprites_json, match_id)
    return HTMLResponse(content=html)


@router.get("/{match_id}/share")
async def get_share_link(match_id: str) -> dict:
    """
    Get a shareable link for the match playback.

    Returns the playback viewer URL that can be shared with others.
    """
    match_data = _match_service.get_match(match_id)
    if match_data is None:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    return {
        "match_id": match_id,
        "playback_url": f"/api/playback/{match_id}/watch",
        "data_url": f"/api/playback/{match_id}",
        "status": match_data.get("status", "unknown"),
    }


# Sprite endpoint at top level
sprite_router = APIRouter(prefix="/sprites", tags=["Sprites"])


@sprite_router.get("/{archetype}")
async def get_sprite(archetype: str) -> dict:
    """Get SVG sprite data for an archetype."""
    archetype = archetype.lower().strip()
    if archetype not in SPRITE_GRIDS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown archetype '{archetype}'",
        )
    return {
        "archetype": archetype,
        "svg": get_sprite_svg(archetype),
    }


def _build_playback_html(playback_json: str, sprites_json: str, match_id: str) -> str:
    """
    Build the self-contained HTML playback viewer.

    Includes:
    - Arena canvas with sprite rendering
    - HP bar overlays
    - Action log panel
    - Speed controls
    - Match summary overlay
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BYTE Wars — Match Playback</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #0a0a1a;
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}}
h1 {{
  color: #00ffcc;
  font-size: 1.5em;
  margin-bottom: 10px;
  text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
}}
.arena {{
  position: relative;
  width: 800px;
  height: 400px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border: 2px solid #00ffcc;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 15px;
}}
.arena-floor {{
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 80px;
  background: linear-gradient(180deg, #2a2a4a 0%, #1a1a3a 100%);
  border-top: 1px solid #333366;
}}
.champion-slot {{
  position: absolute;
  bottom: 90px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s ease;
}}
.champion-slot.attacking {{ animation: attack-lunge 0.4s ease-in-out; }}
.champion-slot.defending {{ animation: defend-glow 0.4s ease-in-out; }}
.champion-slot.hurt {{ animation: hurt-shake 0.3s ease-in-out; }}
.champion-slot.dying {{ animation: death-fade 1s ease-out forwards; }}
.champion-slot.healing {{ animation: heal-glow 0.5s ease-in-out; }}
@keyframes attack-lunge {{
  0%, 100% {{ transform: translateX(0); }}
  50% {{ transform: translateX(30px); }}
}}
@keyframes defend-glow {{
  0%, 100% {{ filter: brightness(1); }}
  50% {{ filter: brightness(1.5) drop-shadow(0 0 8px #4488cc); }}
}}
@keyframes hurt-shake {{
  0%, 100% {{ transform: translateX(0); }}
  25% {{ transform: translateX(-8px); }}
  75% {{ transform: translateX(8px); }}
}}
@keyframes death-fade {{
  0% {{ opacity: 1; transform: translateY(0); }}
  100% {{ opacity: 0; transform: translateY(20px); }}
}}
@keyframes heal-glow {{
  0%, 100% {{ filter: brightness(1); }}
  50% {{ filter: brightness(1.3) drop-shadow(0 0 10px #44ff44); }}
}}
.sprite-container {{
  width: 64px;
  height: 64px;
}}
.champion-name {{
  font-size: 11px;
  color: #00ffcc;
  margin-top: 4px;
  text-align: center;
  white-space: nowrap;
}}
.hp-bar-bg {{
  width: 70px;
  height: 8px;
  background: #333;
  border-radius: 4px;
  margin-top: 3px;
  overflow: hidden;
}}
.hp-bar {{
  height: 100%;
  background: #44ff44;
  border-radius: 4px;
  transition: width 0.5s ease, background-color 0.3s ease;
}}
.hp-bar.low {{ background: #ff4444; }}
.hp-bar.medium {{ background: #ffaa00; }}
.hp-text {{
  font-size: 9px;
  color: #aaa;
  margin-top: 1px;
}}
.controls {{
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  align-items: center;
}}
.controls button {{
  background: #1a1a3a;
  color: #00ffcc;
  border: 1px solid #00ffcc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  transition: all 0.2s ease;
}}
.controls button:hover {{ background: #00ffcc; color: #0a0a1a; }}
.controls button.active {{ background: #00ffcc; color: #0a0a1a; }}
.speed-label {{ font-size: 12px; color: #888; }}
.turn-display {{
  font-size: 14px;
  color: #ffcc00;
  margin-left: 20px;
}}
.log-panel {{
  width: 800px;
  max-height: 200px;
  overflow-y: auto;
  background: #111122;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 10px;
  font-size: 12px;
  margin-bottom: 15px;
}}
.log-entry {{
  padding: 2px 0;
  border-bottom: 1px solid #1a1a2e;
}}
.log-entry .turn {{ color: #888; }}
.log-entry .action {{ color: #00ffcc; }}
.log-entry .damage {{ color: #ff4444; }}
.log-entry .heal {{ color: #44ff44; }}
.log-entry .death {{ color: #ff6666; font-weight: bold; }}
.damage-popup {{
  position: absolute;
  font-size: 18px;
  font-weight: bold;
  color: #ff4444;
  text-shadow: 0 0 5px #ff0000;
  animation: popup-rise 1s ease-out forwards;
  pointer-events: none;
}}
.damage-popup.heal {{ color: #44ff44; text-shadow: 0 0 5px #00ff00; }}
@keyframes popup-rise {{
  0% {{ opacity: 1; transform: translateY(0); }}
  100% {{ opacity: 0; transform: translateY(-40px); }}
}}
.summary-overlay {{
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
}}
.summary-overlay.visible {{ display: flex; }}
.summary-title {{
  font-size: 24px;
  color: #ffcc00;
  margin-bottom: 15px;
  text-shadow: 0 0 15px rgba(255, 204, 0, 0.5);
}}
.summary-table {{
  border-collapse: collapse;
  font-size: 12px;
}}
.summary-table th {{
  color: #00ffcc;
  padding: 6px 12px;
  border-bottom: 1px solid #333;
  text-align: left;
}}
.summary-table td {{
  padding: 5px 12px;
  border-bottom: 1px solid #222;
}}
.summary-table tr.winner td {{ color: #ffcc00; }}
</style>
</head>
<body>
<h1>BYTE WARS — Match Playback</h1>

<div class="arena" id="arena">
  <div class="arena-floor"></div>
  <div class="summary-overlay" id="summary"></div>
</div>

<div class="controls">
  <button onclick="restart()">Restart</button>
  <button onclick="togglePause()" id="pauseBtn">Pause</button>
  <span class="speed-label">Speed:</span>
  <button onclick="setSpeed(0.5)" id="speed05">0.5x</button>
  <button onclick="setSpeed(1)" id="speed1" class="active">1x</button>
  <button onclick="setSpeed(2)" id="speed2">2x</button>
  <button onclick="skipToEnd()">Skip to End</button>
  <span class="turn-display" id="turnDisplay">Turn: 0</span>
</div>

<div class="log-panel" id="logPanel"></div>

<script>
const PLAYBACK = {playback_json};
const SPRITES = {sprites_json};
const MATCH_ID = "{match_id}";

let currentEventIndex = 0;
let speed = 1;
let paused = false;
let timer = null;
let championElements = {{}};
let hpState = {{}};

// Position champions evenly across the arena
const POSITIONS = [
  {{ left: 100, bottom: 90 }},
  {{ left: 600, bottom: 90 }},
  {{ left: 250, bottom: 90 }},
  {{ left: 450, bottom: 90 }},
];

function init() {{
  const arena = document.getElementById('arena');

  PLAYBACK.champions.forEach((champ, i) => {{
    const pos = POSITIONS[i] || POSITIONS[0];
    const slot = document.createElement('div');
    slot.className = 'champion-slot';
    slot.id = `champ-${{champ.id}}`;
    slot.style.left = pos.left + 'px';
    slot.style.bottom = pos.bottom + 'px';

    const spriteDiv = document.createElement('div');
    spriteDiv.className = 'sprite-container';
    spriteDiv.innerHTML = SPRITES[champ.archetype] || SPRITES['ranger'];

    const nameEl = document.createElement('div');
    nameEl.className = 'champion-name';
    nameEl.textContent = champ.name;

    const hpBarBg = document.createElement('div');
    hpBarBg.className = 'hp-bar-bg';
    const hpBar = document.createElement('div');
    hpBar.className = 'hp-bar';
    hpBar.id = `hp-${{champ.id}}`;
    hpBar.style.width = '100%';
    hpBarBg.appendChild(hpBar);

    const hpText = document.createElement('div');
    hpText.className = 'hp-text';
    hpText.id = `hptext-${{champ.id}}`;
    hpText.textContent = `${{champ.max_hp}}/${{champ.max_hp}}`;

    slot.appendChild(spriteDiv);
    slot.appendChild(nameEl);
    slot.appendChild(hpBarBg);
    slot.appendChild(hpText);
    arena.appendChild(slot);

    championElements[champ.id] = slot;
    hpState[champ.id] = {{ current: champ.max_hp, max: champ.max_hp }};
  }});

  playNextEvent();
}}

function playNextEvent() {{
  if (paused || currentEventIndex >= PLAYBACK.events.length) return;

  const event = PLAYBACK.events[currentEventIndex];
  processEvent(event);
  currentEventIndex++;

  if (currentEventIndex < PLAYBACK.events.length) {{
    const nextEvent = PLAYBACK.events[currentEventIndex];
    const delay = Math.max(50, event.duration / speed);
    timer = setTimeout(playNextEvent, delay);
  }}
}}

function processEvent(event) {{
  const type = event.type;
  const slot = championElements[event.champion_id];

  switch (type) {{
    case 'match_start':
      addLog('match_start', `Match begins! ${{event.data.champion_count}} champions enter the arena.`);
      break;

    case 'turn_start':
      document.getElementById('turnDisplay').textContent = `Turn: ${{event.data.turn_number}}`;
      if (event.data.used_fallback) {{
        addLog('turn', `Turn ${{event.data.turn_number}}: ${{event.champion_name}} (AI timeout — random actions)`);
      }}
      break;

    case 'attack':
      if (slot) triggerAnim(slot, 'attacking');
      addLog('action', `${{event.champion_name}} uses ${{event.data.action}} on ${{event.target_name}} (-${{Math.round(event.data.damage)}} HP)`);
      break;

    case 'damage_taken':
      const targetSlot = championElements[event.champion_id];
      if (targetSlot) {{
        triggerAnim(targetSlot, 'hurt');
        showDamagePopup(targetSlot, event.data.damage, false);
      }}
      updateHp(event.champion_id, event.data.hp_after);
      break;

    case 'defend':
      if (slot) triggerAnim(slot, 'defending');
      addLog('action', `${{event.champion_name}} defends! (30% damage reduction)`);
      break;

    case 'heal':
      if (slot) triggerAnim(slot, 'healing');
      if (event.data.heal_amount > 0) {{
        showDamagePopup(slot, event.data.heal_amount, true);
      }}
      updateHp(event.champion_id, event.data.hp_after);
      addLog('heal', `${{event.champion_name}} heals for ${{Math.round(event.data.heal_amount)}} HP`);
      break;

    case 'death':
      const deadSlot = championElements[event.champion_id];
      if (deadSlot) {{
        deadSlot.classList.add('dying');
      }}
      addLog('death', `${{event.champion_name}} has been eliminated by ${{event.data.killed_by_name}}!`);
      break;

    case 'match_end':
      showSummary(event.data);
      if (event.data.winner_name) {{
        addLog('match_start', `MATCH OVER — ${{event.data.winner_name}} wins!`);
      }} else {{
        addLog('match_start', `MATCH OVER — ${{event.data.status}}`);
      }}
      break;
  }}
}}

function updateHp(champId, newHp) {{
  const state = hpState[champId];
  if (!state) return;
  state.current = Math.max(0, newHp);
  const pct = (state.current / state.max) * 100;
  const bar = document.getElementById(`hp-${{champId}}`);
  const text = document.getElementById(`hptext-${{champId}}`);
  if (bar) {{
    bar.style.width = pct + '%';
    bar.className = 'hp-bar' + (pct < 25 ? ' low' : pct < 50 ? ' medium' : '');
  }}
  if (text) text.textContent = `${{Math.round(state.current)}}/${{state.max}}`;
}}

function triggerAnim(slot, className) {{
  slot.classList.remove('attacking', 'defending', 'hurt', 'healing');
  void slot.offsetWidth; // force reflow
  slot.classList.add(className);
  setTimeout(() => slot.classList.remove(className), 600);
}}

function showDamagePopup(slot, amount, isHeal) {{
  if (!slot) return;
  const popup = document.createElement('div');
  popup.className = 'damage-popup' + (isHeal ? ' heal' : '');
  popup.textContent = (isHeal ? '+' : '-') + Math.round(amount);
  popup.style.left = '20px';
  popup.style.top = '-10px';
  slot.appendChild(popup);
  setTimeout(() => popup.remove(), 1000);
}}

function addLog(type, message) {{
  const panel = document.getElementById('logPanel');
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `<span class="${{type}}">${{message}}</span>`;
  panel.appendChild(entry);
  panel.scrollTop = panel.scrollHeight;
}}

function showSummary(data) {{
  const overlay = document.getElementById('summary');
  let html = '<div class="summary-title">';
  if (data.winner_name) {{
    html += `${{data.winner_name}} WINS!`;
  }} else {{
    html += `MATCH ${{data.status.toUpperCase()}}`;
  }}
  html += `</div><div style="color:#888;margin-bottom:15px;">Turns: ${{data.total_turns}}</div>`;

  html += '<table class="summary-table"><tr><th>Champion</th><th>Damage</th><th>Taken</th><th>Healed</th><th>Kills</th></tr>';
  for (const [id, stats] of Object.entries(PLAYBACK.summary)) {{
    const isWinner = id === data.winner_id;
    html += `<tr class="${{isWinner ? 'winner' : ''}}">`;
    html += `<td>${{stats.name}}${{isWinner ? ' ★' : ''}}</td>`;
    html += `<td>${{Math.round(stats.damage_dealt)}}</td>`;
    html += `<td>${{Math.round(stats.damage_taken)}}</td>`;
    html += `<td>${{Math.round(stats.healing_done)}}</td>`;
    html += `<td>${{stats.kills}}</td></tr>`;
  }}
  html += '</table>';

  overlay.innerHTML = html;
  overlay.classList.add('visible');
}}

function setSpeed(s) {{
  speed = s;
  document.querySelectorAll('.controls button[id^=speed]').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('speed' + String(s).replace('.', ''));
  if (btn) btn.classList.add('active');
}}

function togglePause() {{
  paused = !paused;
  document.getElementById('pauseBtn').textContent = paused ? 'Play' : 'Pause';
  if (!paused) playNextEvent();
}}

function restart() {{
  clearTimeout(timer);
  paused = false;
  currentEventIndex = 0;
  document.getElementById('pauseBtn').textContent = 'Pause';
  document.getElementById('logPanel').innerHTML = '';
  document.getElementById('summary').classList.remove('visible');
  document.getElementById('summary').innerHTML = '';

  // Reset champions
  PLAYBACK.champions.forEach(champ => {{
    const slot = championElements[champ.id];
    if (slot) {{
      slot.className = 'champion-slot';
      slot.style.opacity = '1';
    }}
    hpState[champ.id] = {{ current: champ.max_hp, max: champ.max_hp }};
    updateHp(champ.id, champ.max_hp);
  }});

  playNextEvent();
}}

function skipToEnd() {{
  clearTimeout(timer);
  while (currentEventIndex < PLAYBACK.events.length) {{
    const event = PLAYBACK.events[currentEventIndex];
    processEvent(event);
    currentEventIndex++;
  }}
}}

window.addEventListener('load', init);
</script>
</body>
</html>"""
