import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPlayback, getPlaybackUrl, getMatchWagers, getMatch } from '../services/api';
import {
  PixelButton, Pill, HPBar, Sprite, archetypeSprite, Panel, ItemIcon, rarityColor, SolDiamond,
} from '../ui/primitives';
import { ArenaBg, ARENA_LANDMARKS, Landmark } from '../ui/arena';

const STATUS_COLORS = {
  won: 'var(--bw-acid)',
  lost: 'var(--bw-blood)',
  refunded: 'var(--bw-yellow)',
  locked: 'var(--bw-cyan)',
  placed: 'var(--bw-ink-dim)',
  cancelled: 'var(--bw-ink-low)',
};

export default function PlaybackPage() {
  const { matchId } = useParams();
  const [playback, setPlayback] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [wagers, setWagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showViewer, setShowViewer] = useState(false);
  const [theme, setTheme] = useState('forest');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getPlayback(matchId).catch(e => { setError(e.message); return null; }),
      getMatchWagers(matchId).catch(() => []),
      getMatch(matchId).catch(() => null),
    ]).then(([pb, ws, md]) => {
      setPlayback(pb);
      setWagers(ws || []);
      setMatchData(md);
    }).finally(() => setLoading(false));
  }, [matchId]);

  // Cycle theme based on matchId hash so each match gets a flavor
  useEffect(() => {
    const themes = ['forest', 'ruins', 'ice'];
    const hash = (matchId || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    setTheme(themes[hash % themes.length]);
  }, [matchId]);

  const totalPot = wagers.reduce((sum, w) => sum + (w.amount_sol || 0), 0);

  const champions = useMemo(() => {
    if (!playback?.summary) return [];
    return Object.entries(playback.summary).map(([id, stats]) => ({ id, ...stats }));
  }, [playback]);

  if (loading) return <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING PLAYBACK…</div>;
  if (error) return <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>;
  if (!playback) return null;

  return (
    <div className="bw-stack-lg">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <h1 className="bw-h1" style={{ marginBottom: 0 }}>{'>'} REPLAY · {matchId.slice(0, 8)}</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <PixelButton variant="ghost" onClick={() => setShowViewer(v => !v)}>
            {showViewer ? 'HIDE VIEWER' : 'OPEN VIEWER'}
          </PixelButton>
          <Link to="/history" style={{ textDecoration: 'none' }}>
            <PixelButton variant="ghost">HISTORY</PixelButton>
          </Link>
        </div>
      </div>

      {/* HP / status strip */}
      <Panel>
        <div className="bw-h3">CHAMPIONS</div>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {champions.map(c => {
            const isWinner = c.id === playback.winner_id;
            const archetype = c.archetype || 'tank';
            const maxHp = (c.max_health ?? c.starting_health ?? 100);
            const remainingHp = Math.max(0, maxHp - (c.damage_taken ?? 0));
            const ratio = Math.max(0, Math.min(1, remainingHp / Math.max(1, maxHp)));
            return (
              <div key={c.id} style={{
                padding: 10,
                background: 'var(--bw-bg)',
                boxShadow: isWinner
                  ? 'inset 0 0 0 2px var(--bw-acid), 0 0 12px rgba(182,255,60,0.3)'
                  : 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Sprite kind={archetypeSprite(archetype)} scale={2}
                    style={{ opacity: isWinner ? 1 : (remainingHp > 0 ? 1 : 0.3) }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: isWinner ? 'var(--bw-acid)' : 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {(c.name || '').toUpperCase()}
                      {isWinner && <span style={{ color: 'var(--bw-yellow)' }}> ★</span>}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                      {Math.round(remainingHp)}/{Math.round(maxHp)} HP
                    </div>
                  </div>
                </div>
                <HPBar value={ratio} segments={16} />
              </div>
            );
          })}
        </div>
      </Panel>

      {/* ARENA */}
      <Panel style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ position: 'relative', height: 320, overflow: 'hidden', background: '#000' }}>
          <ArenaBg theme={theme} />
          {(ARENA_LANDMARKS[theme] || []).map((lm, i) => (
            <Landmark
              key={i}
              kind={lm.kind}
              scale={lm.scale * 1.5}
              style={{ left: lm.left, bottom: lm.bottom, transform: 'translateX(-50%)', zIndex: 2 }}
            />
          ))}
          {/* Champions placed evenly on the floor */}
          {champions.map((c, i) => {
            const isWinner = c.id === playback.winner_id;
            const remainingHp = Math.max(0, ((c.max_health ?? c.starting_health ?? 100) - (c.damage_taken ?? 0)));
            const alive = remainingHp > 0;
            const left = `${10 + (i * 80) / Math.max(1, champions.length - 1)}%`;
            return (
              <div
                key={c.id}
                style={{
                  position: 'absolute',
                  left,
                  bottom: 30,
                  transform: 'translateX(-50%)',
                  zIndex: 3,
                  filter: alive ? 'none' : 'grayscale(1)',
                  opacity: alive ? 1 : 0.4,
                }}
              >
                <Sprite kind={archetypeSprite(c.archetype || 'tank')} scale={5}
                  glow={isWinner ? 'var(--bw-acid)' : null}
                  className={alive ? 'bob' : ''} />
                {!alive && (
                  <div style={{
                    position: 'absolute', top: -18, left: '50%', transform: 'translateX(-50%)',
                    fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-blood)',
                    letterSpacing: '0.1em',
                  }}>DEFEATED</div>
                )}
                {isWinner && (
                  <div style={{
                    position: 'absolute', top: -22, left: '50%', transform: 'translateX(-50%)',
                    fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-yellow)',
                    letterSpacing: '0.1em',
                  }}>★ VICTOR</div>
                )}
              </div>
            );
          })}
        </div>

        {/* THEME SELECTOR + STATUS */}
        <div style={{ padding: 10, display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between', borderTop: '2px solid var(--bw-line)', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {['forest', 'ruins', 'ice'].map(t => (
              <button key={t} type="button" onClick={() => setTheme(t)}
                style={{
                  all: 'unset', cursor: 'pointer',
                  fontFamily: 'var(--font-pixel)', fontSize: 7, letterSpacing: '0.1em',
                  padding: '4px 8px',
                  background: theme === t ? 'var(--bw-cyan)' : 'var(--bw-panel-2)',
                  color: theme === t ? '#001214' : 'var(--bw-ink-dim)',
                }}>
                {t.toUpperCase()}
              </button>
            ))}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            <span style={{ color: 'var(--bw-ink-low)' }}>STATUS · </span>
            <span style={{ color: playback.status === 'complete' ? 'var(--bw-acid)' : 'var(--bw-yellow)' }}>{(playback.status || '').toUpperCase()}</span>
            <span style={{ color: 'var(--bw-ink-low)' }}> · TURNS </span>
            <span style={{ color: 'var(--bw-ink)' }}>{playback.total_turns}</span>
          </div>
        </div>
      </Panel>

      {/* EMBEDDED PLAYBACK VIEWER */}
      {showViewer && (
        <Panel style={{ padding: 0 }}>
          <iframe
            src={getPlaybackUrl(matchId)}
            style={{ width: '100%', height: 600, border: 0, background: '#0a0a12' }}
            title="Match Playback"
          />
        </Panel>
      )}

      {/* CHAMPION STATS */}
      <Panel>
        <div className="bw-h3">COMBAT REPORT</div>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {champions.map(c => {
            const isWinner = c.id === playback.winner_id;
            return (
              <div key={c.id} style={{
                padding: 10,
                background: 'var(--bw-bg)',
                boxShadow: isWinner
                  ? 'inset 0 0 0 2px var(--bw-acid)'
                  : 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: isWinner ? 'var(--bw-acid)' : 'var(--bw-ink)' }}>
                    {(c.name || '').toUpperCase()}{isWinner && ' ★'}
                  </span>
                  <Pill color="var(--bw-line)" textColor="var(--bw-ink-dim)">{c.archetype || '?'}</Pill>
                </div>
                <Row label="DMG DEALT"  value={Math.round(c.damage_dealt ?? 0)} color="var(--bw-blood)" />
                <Row label="DMG TAKEN"  value={Math.round(c.damage_taken ?? 0)} color="var(--bw-yellow)" />
                <Row label="HEAL"       value={Math.round(c.healing_done ?? 0)} color="var(--bw-acid)" />
                <Row label="KILLS"      value={c.kills ?? 0} color="var(--bw-magenta)" />
                <Row label="ACTIONS"    value={c.actions_taken ?? 0} color="var(--bw-cyan)" />
              </div>
            );
          })}
        </div>
      </Panel>

      {/* EVENT LOG */}
      {playback.events && playback.events.length > 0 && (
        <Panel>
          <div className="bw-h3">EVENT LOG · {playback.events.length}</div>
          <div className="panel-sunken" style={{ padding: 10, maxHeight: 280, overflowY: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, background: '#000' }}>
            {playback.events.map((ev, i) => <EventLine key={i} idx={i} ev={ev} />)}
          </div>
        </Panel>
      )}

      {/* WAGERS */}
      {wagers.length > 0 && (
        <Panel>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div className="bw-h3" style={{ marginBottom: 0 }}>WAGER POOL</div>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-yellow)', fontSize: 12, fontWeight: 800 }}>
              <SolDiamond /> {totalPot.toFixed(2)} SOL
            </span>
          </div>
          <div className="bw-stack">
            {wagers.map(w => (
              <div key={w.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                  {(w.wallet_address || '').slice(0, 14)}… · {w.amount_sol} SOL
                </span>
                <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.08em', color: STATUS_COLORS[w.status] || 'var(--bw-ink)' }}>
                  {(w.status || '').toUpperCase()}
                  {w.status === 'won' && ` +${(w.payout_sol - w.amount_sol).toFixed(2)}`}
                  {w.status === 'refunded' && ` ${w.payout_sol.toFixed(2)}`}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* LOOT */}
      {matchData?.loot_chest_items && matchData.loot_chest_items.length > 0 && (
        <Panel>
          <div className="bw-h3">{'>>'} LOOT DROP · {matchData.loot_chest_items.length} ITEMS</div>
          <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
            {matchData.loot_chest_items.map((item, i) => (
              <div key={i} style={{
                padding: 8,
                background: 'var(--bw-bg)',
                boxShadow: `inset 0 0 0 2px ${rarityColor(item.rarity)}`,
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <ItemIcon kind={iconForItem(item)} scale={2} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {(item.name || '').replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: rarityColor(item.rarity) }}>
                    {(item.rarity || '').toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, padding: '2px 0' }}>
      <span style={{ color: 'var(--bw-ink-dim)', letterSpacing: '0.06em' }}>{label}</span>
      <span style={{ color, fontWeight: 800 }}>{value}</span>
    </div>
  );
}

function EventLine({ idx, ev }) {
  // Tolerate the engine's various event shapes
  const text = ev.text || ev.message || ev.description ||
    `${ev.actor || ''} ${ev.action || ev.type || ''}${ev.target ? ' → ' + ev.target : ''}${ev.damage ? ' (' + ev.damage + ')' : ''}`;
  const turn = ev.turn ?? ev.t ?? idx;
  return (
    <div style={{ display: 'flex', gap: 8, padding: '2px 0', color: 'var(--bw-ink)' }}>
      <span style={{ color: 'var(--bw-ink-low)', minWidth: 32 }}>T{String(turn).padStart(2, '0')}</span>
      <span style={{ color: 'var(--bw-acid)' }}>{'>'}</span>
      <span style={{ flex: 1 }}>{text}</span>
    </div>
  );
}

function iconForItem(item) {
  const t = item.nft_type || '';
  if (t === 'gear') return 'sword';
  if (t === 'skill') return 'staff';
  return 'scroll';
}
