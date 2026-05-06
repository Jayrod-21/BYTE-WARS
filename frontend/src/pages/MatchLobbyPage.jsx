import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  listChampions, listMatches, createMatch, startMatch,
  placeWager, getMatchOdds, getUser,
} from '../services/api';
import { requestNotificationPermission, notifyMatchComplete } from '../services/notifications';
import {
  PixelButton, Pill, Sprite, archetypeSprite, Ticker, SolDiamond, Panel,
} from '../ui/primitives';

export default function MatchLobbyPage() {
  const navigate = useNavigate();
  const user = getUser();

  const [champions, setChampions] = useState([]);
  const [recentMatches, setRecentMatches] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fighting, setFighting] = useState(false);
  const [error, setError] = useState('');

  // Wager
  const [wagerEnabled, setWagerEnabled] = useState(false);
  const [wagerChampion, setWagerChampion] = useState('');
  const [wagerAmount, setWagerAmount] = useState(0.1);
  const [matchId, setMatchId] = useState(null);
  const [odds, setOdds] = useState(null);
  const [wagerPlaced, setWagerPlaced] = useState(false);

  useEffect(() => {
    Promise.all([listChampions(), listMatches()])
      .then(([champs, matches]) => {
        setChampions(champs || []);
        const sorted = (matches || [])
          .filter(m => m.status === 'complete' || m.status === 'timed_out')
          .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
          .slice(0, 8);
        setRecentMatches(sorted);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function toggleSelect(id) {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev,
    );
    setMatchId(null);
    setOdds(null);
    setWagerPlaced(false);
  }

  async function handlePlaceWager() {
    if (!matchId || !wagerChampion) return;
    setError('');
    try {
      const walletAddr = user?.wallet_address || `devnet_${user?.id || 'anon'}`;
      await placeWager(matchId, user?.id || 'anon', walletAddr, wagerChampion, parseFloat(wagerAmount));
      setWagerPlaced(true);
      const newOdds = await getMatchOdds(matchId);
      setOdds(newOdds);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleQueueUp() {
    if (selected.length < 2) { setError('Pick at least 2 champions'); return; }
    setError('');
    setFighting(true);
    try {
      let mid = matchId;
      if (!mid) {
        const match = await createMatch(selected);
        mid = match.id;
        setMatchId(mid);
      }
      await requestNotificationPermission();
      const result = await startMatch(mid);
      notifyMatchComplete(mid, result.winner_name);
      navigate(`/playback/${mid}`);
    } catch (err) {
      setError(err.message);
      setFighting(false);
    }
  }

  async function ensureMatch() {
    if (matchId) return matchId;
    if (selected.length < 2) { setError('Pick at least 2 champions first'); return null; }
    try {
      const match = await createMatch(selected);
      setMatchId(match.id);
      return match.id;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }

  const selectedChampions = champions.filter(c => selected.includes(c.id));

  const tickerItems = recentMatches.length > 0
    ? recentMatches.map(m => `${(m.winner_name || '???').toUpperCase()} CRUSHED ${(m.champion_names || []).filter(n => n !== m.winner_name).join(' / ').toUpperCase()}`)
    : ['QUEUE FOR THE NEXT BATTLE', 'DEPLOY YOUR CHAMPION', 'WAGER YOUR SOL'];

  return (
    <div className="bw-stack-lg">
      <Ticker items={tickerItems} />

      <h1 className="bw-h1">{'>'} ARENA / LOBBY</h1>

      {error && <ErrorPill text={error} />}

      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'minmax(0, 1fr)' }}>
        {/* QUEUE PANEL */}
        <Panel style={{ padding: 16 }}>
          <h2 className="bw-h2" style={{ color: 'var(--bw-acid)' }}>{'>>'} QUEUE UP</h2>

          <div style={{ marginBottom: 12, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)' }}>
            PICK 2–4 CHAMPIONS · {selected.length} SELECTED
          </div>

          {loading && <Skeleton lines={3} />}

          {!loading && champions.length === 0 && (
            <div className="panel-sunken" style={{ padding: 14, textAlign: 'center' }}>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO CHAMPIONS YET</div>
              <Link to="/champions/new" style={{ display: 'inline-block', marginTop: 10 }}>
                <PixelButton variant="acid">FORGE YOUR FIRST CHAMPION</PixelButton>
              </Link>
            </div>
          )}

          {!loading && champions.length > 0 && (
            <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {champions.map(c => {
                const isSelected = selected.includes(c.id);
                const sprite = archetypeSprite(c.archetype);
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => toggleSelect(c.id)}
                    style={{
                      all: 'unset',
                      cursor: 'pointer',
                      display: 'flex', gap: 10, padding: 10,
                      background: isSelected ? 'rgba(182,255,60,0.08)' : 'var(--bw-bg-2)',
                      boxShadow: isSelected
                        ? 'inset 0 0 0 2px var(--bw-acid), 0 0 0 0 #000, 0 4px 0 0 #000'
                        : 'inset -2px -2px 0 0 #000, inset 2px 2px 0 0 var(--bw-line-2), 0 4px 0 0 #000',
                    }}
                  >
                    <Sprite kind={sprite} scale={2} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, letterSpacing: '0.05em', color: 'var(--bw-ink)', marginBottom: 4 }}>
                        {c.name?.toUpperCase()}
                      </div>
                      <div style={{ display: 'flex', gap: 4, marginBottom: 4, flexWrap: 'wrap' }}>
                        <Pill color="var(--bw-cyan)">{c.archetype}</Pill>
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                        HP {c.stats.health} · STR {c.stats.strength} · END {c.stats.endurance}
                      </div>
                    </div>
                    {isSelected && (
                      <div style={{
                        fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-acid)',
                        alignSelf: 'flex-start',
                      }}>✓</div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Wager */}
          {selected.length >= 2 && (
            <div style={{ marginTop: 16, padding: 12, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-yellow)', letterSpacing: '0.08em' }}>
                  ◇ OPTIONAL WAGER
                </span>
                <PixelButton variant={wagerEnabled ? 'magenta' : 'ghost'} onClick={async () => {
                  const next = !wagerEnabled;
                  setWagerEnabled(next);
                  if (next && !matchId) await ensureMatch();
                }} style={{ padding: '6px 10px', fontSize: 8 }}>
                  {wagerEnabled ? 'CANCEL' : 'ADD WAGER'}
                </PixelButton>
              </div>

              {wagerEnabled && !wagerPlaced && (
                <div className="bw-stack">
                  <div>
                    <Label>BET ON</Label>
                    <select value={wagerChampion} onChange={e => setWagerChampion(e.target.value)} style={{ width: '100%' }}>
                      <option value="">— select champion —</option>
                      {selectedChampions.map(c => (
                        <option key={c.id} value={c.id}>{c.name} ({c.archetype})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>AMOUNT · {wagerAmount.toFixed(2)} SOL</Label>
                    <input
                      type="range"
                      min="0.1" max="10" step="0.1"
                      value={wagerAmount}
                      onChange={e => setWagerAmount(parseFloat(e.target.value))}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <PixelButton variant="yellow" onClick={handlePlaceWager} disabled={!wagerChampion} full
                    style={{ background: 'var(--bw-yellow)', color: '#1a1400' }}>
                    PLACE BET ◇ {wagerAmount.toFixed(2)}
                  </PixelButton>
                </div>
              )}

              {wagerPlaced && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-acid)' }}>
                  ✓ WAGER LOCKED · {wagerAmount.toFixed(2)} SOL on {selectedChampions.find(c => c.id === wagerChampion)?.name}
                </div>
              )}

              {odds?.odds_by_champion && Object.keys(odds.odds_by_champion).length > 0 && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: '2px dashed var(--bw-line)' }}>
                  <Label>POOL</Label>
                  {Object.values(odds.odds_by_champion).map(o => (
                    <div key={o.champion_id} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, padding: '2px 0' }}>
                      <span style={{ color: 'var(--bw-ink-dim)' }}>{selectedChampions.find(c => c.id === o.champion_id)?.name || o.champion_id.slice(0, 8)}</span>
                      <span style={{ color: 'var(--bw-yellow)' }}>{o.implied_odds}× · {o.total_wagered} SOL</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <PixelButton variant="acid" full disabled={selected.length < 2 || fighting} onClick={handleQueueUp}
              style={{ height: 56, fontSize: 12 }}>
              {fighting ? 'FINDING MATCH…' : `QUEUE UP ⚔ ${selected.length}/4`}
            </PixelButton>
          </div>
        </Panel>

        {/* MATCH FEED */}
        <Panel>
          <h2 className="bw-h2">{'>'} LIVE FEED</h2>
          {recentMatches.length === 0 && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)' }}>
              NO MATCHES YET. BE THE FIRST TO QUEUE.
            </div>
          )}
          <div className="bw-stack">
            {recentMatches.map(m => (
              <Link key={m.id} to={`/playback/${m.id}`} style={{
                display: 'block', padding: 10, background: 'var(--bw-bg)',
                boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line-2)',
                textDecoration: 'none', color: 'inherit',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <span style={{ color: 'var(--bw-acid)', fontWeight: 800 }}>{m.winner_name || '???'}</span>
                    <span style={{ color: 'var(--bw-ink-low)' }}> def. </span>
                    <span style={{ color: 'var(--bw-ink-dim)' }}>{(m.champion_names || []).filter(n => n !== m.winner_name).join(', ')}</span>
                  </div>
                  <Pill color="var(--bw-line-2)" textColor="var(--bw-ink)">{m.total_turns}T</Pill>
                </div>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Label({ children }) {
  return <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 4, textTransform: 'uppercase' }}>{children}</div>;
}

function ErrorPill({ text }) {
  return (
    <div style={{
      fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-blood)',
      padding: '8px 10px', background: 'rgba(255,60,92,0.08)',
      boxShadow: 'inset 0 0 0 2px var(--bw-blood)',
    }}>! {text}</div>
  );
}

function Skeleton({ lines = 3 }) {
  return (
    <div className="bw-stack">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} style={{ height: 56, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }} />
      ))}
    </div>
  );
}
