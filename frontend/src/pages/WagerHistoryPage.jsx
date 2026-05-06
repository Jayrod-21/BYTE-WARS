import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  getUserWagers, getUser, getWalletBalance, listMatches,
  getMatchOdds, placeWager, airdropSol,
} from '../services/api';
import {
  PixelButton, Pill, Panel, SolDiamond, Sprite, archetypeSprite,
} from '../ui/primitives';

const STATUS_COLORS = {
  won: 'var(--bw-acid)',
  lost: 'var(--bw-blood)',
  refunded: 'var(--bw-yellow)',
  locked: 'var(--bw-cyan)',
  placed: 'var(--bw-ink-dim)',
  cancelled: 'var(--bw-ink-low)',
};

function isWeekRecent(iso) {
  if (!iso) return false;
  const t = new Date(iso).getTime();
  return Date.now() - t < 7 * 24 * 3600 * 1000;
}

export default function WagerHistoryPage() {
  const user = getUser();

  const [wagers, setWagers] = useState([]);
  const [balance, setBalance] = useState(null);
  const [pending, setPending] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [featuredOdds, setFeaturedOdds] = useState(null);
  const [betChampion, setBetChampion] = useState('');
  const [betAmount, setBetAmount] = useState(0.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [airdropping, setAirdropping] = useState(false);

  const wallet = user ? (user.wallet_address || `devnet_${user.id}`) : null;

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    Promise.all([
      getUserWagers(user.id).catch(() => []),
      getWalletBalance(wallet).catch(() => null),
      listMatches('pending').catch(() => []),
    ]).then(([w, bal, matches]) => {
      setWagers(w || []);
      setBalance(bal?.balance_sol ?? bal?.balance ?? 0);
      const pendingMatches = (matches || []).filter(m => m.status === 'pending' || m.status === 'created');
      setPending(pendingMatches);
      if (pendingMatches[0]) loadFeatured(pendingMatches[0]);
    }).finally(() => setLoading(false));
  }, [user?.id]);

  async function loadFeatured(match) {
    setFeatured(match);
    try {
      const o = await getMatchOdds(match.id);
      setFeaturedOdds(o);
    } catch { setFeaturedOdds(null); }
  }

  async function handleAirdrop() {
    if (!wallet) return;
    setAirdropping(true);
    try {
      await airdropSol(wallet, 5);
      const bal = await getWalletBalance(wallet);
      setBalance(bal?.balance_sol ?? bal?.balance ?? 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setAirdropping(false);
    }
  }

  async function handlePlaceBet() {
    if (!featured || !betChampion) return;
    setError('');
    try {
      await placeWager(featured.id, user.id, wallet, betChampion, parseFloat(betAmount));
      // Refresh
      const [w, bal, o] = await Promise.all([
        getUserWagers(user.id),
        getWalletBalance(wallet),
        getMatchOdds(featured.id),
      ]);
      setWagers(w);
      setBalance(bal?.balance_sol ?? bal?.balance ?? 0);
      setFeaturedOdds(o);
    } catch (err) {
      setError(err.message);
    }
  }

  const stats = useMemo(() => {
    const totalWagered = wagers.reduce((s, w) => s + (w.amount_sol || 0), 0);
    const won = wagers.filter(w => w.status === 'won').reduce((s, w) => s + (w.payout_sol || 0), 0);
    const lost = wagers.filter(w => w.status === 'lost').reduce((s, w) => s + (w.amount_sol || 0), 0);
    const weekly = wagers
      .filter(w => isWeekRecent(w.created_at))
      .reduce((s, w) => s + (w.status === 'won' ? (w.payout_sol - w.amount_sol) : w.status === 'lost' ? -w.amount_sol : 0), 0);
    return { totalWagered, won, lost, net: won - lost, weekly };
  }, [wagers]);

  if (!user) {
    return (
      <Panel>
        <h1 className="bw-h1">{'>'} WALLET / LOG IN REQUIRED</h1>
        <Link to="/login"><PixelButton variant="acid">LOG IN</PixelButton></Link>
      </Panel>
    );
  }

  return (
    <div className="bw-stack-lg">
      {/* HEADER */}
      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div className="bw-h3">BALANCE</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 800, color: 'var(--bw-yellow)' }}>
              <SolDiamond size={14} /> {balance == null ? '…' : Number(balance).toFixed(2)} <span style={{ fontSize: 14, color: 'var(--bw-ink-low)' }}>SOL</span>
            </div>
            <div style={{ marginTop: 6, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-low)' }}>
              {wallet}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="bw-h3">7-DAY P&L</div>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: 22, fontWeight: 800,
              color: stats.weekly >= 0 ? 'var(--bw-acid)' : 'var(--bw-blood)',
            }}>
              {stats.weekly >= 0 ? '+' : ''}{stats.weekly.toFixed(2)} SOL
            </div>
            <div style={{ marginTop: 8 }}>
              <PixelButton variant="ghost" onClick={handleAirdrop} disabled={airdropping}>
                {airdropping ? 'AIRDROPPING…' : 'AIRDROP +5 SOL'}
              </PixelButton>
            </div>
          </div>
        </div>
      </Panel>

      {error && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>}

      {/* FEATURED MATCH (live betting) */}
      {featured && (
        <Panel>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="bw-h3" style={{ marginBottom: 0 }}>FEATURED MATCH · LIVE BET</div>
            {pending.length > 1 && (
              <select value={featured.id} onChange={e => loadFeatured(pending.find(p => p.id === e.target.value))}
                style={{ fontSize: 11 }}>
                {pending.map(p => <option key={p.id} value={p.id}>{p.id.slice(0, 8)} · {(p.champion_names || []).join(' / ')}</option>)}
              </select>
            )}
          </div>

          <div style={{ display: 'flex', gap: 14, alignItems: 'center', justifyContent: 'space-around', flexWrap: 'wrap', padding: 14, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
            {(featured.champion_ids || []).slice(0, 4).map((cid, i) => {
              const name = featured.champion_names?.[i];
              const arch = featured.champion_archetypes?.[i] || 'tank';
              const oddsRow = featuredOdds?.odds_by_champion?.[cid];
              const isPicked = betChampion === cid;
              return (
                <button
                  type="button"
                  key={cid}
                  onClick={() => setBetChampion(cid)}
                  style={{
                    all: 'unset', cursor: 'pointer',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                    padding: 10,
                    boxShadow: isPicked ? 'inset 0 0 0 2px var(--bw-acid)' : 'none',
                    minWidth: 100,
                  }}
                >
                  <Sprite kind={archetypeSprite(arch)} scale={3} glow={isPicked ? 'var(--bw-acid)' : null} />
                  <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: isPicked ? 'var(--bw-acid)' : 'var(--bw-ink)', letterSpacing: '0.05em' }}>
                    {(name || '').toUpperCase()}
                  </div>
                  {oddsRow && (
                    <Pill color="var(--bw-yellow)">{oddsRow.implied_odds}×</Pill>
                  )}
                </button>
              );
            })}
          </div>

          <div style={{ marginTop: 14 }}>
            <div className="bw-h3">BET AMOUNT · {betAmount.toFixed(2)} SOL</div>
            <input type="range" min="0.1" max={Math.max(0.1, balance || 1)} step="0.1"
              value={betAmount} onChange={e => setBetAmount(parseFloat(e.target.value))}
              style={{ width: '100%' }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', margin: '6px 0 12px' }}>
            <span>POTENTIAL PAYOUT</span>
            <span style={{ color: 'var(--bw-yellow)', fontWeight: 800 }}>
              ◇ {betChampion && featuredOdds?.odds_by_champion?.[betChampion]
                ? (betAmount * featuredOdds.odds_by_champion[betChampion].implied_odds).toFixed(2)
                : '—'} SOL
            </span>
          </div>

          <PixelButton variant="acid" full disabled={!betChampion} onClick={handlePlaceBet} style={{ height: 52, fontSize: 12 }}>
            PLACE BET ◇ {betAmount.toFixed(2)}
          </PixelButton>
        </Panel>
      )}

      {!featured && pending.length === 0 && (
        <Panel><div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO LIVE MATCHES TO BET ON. <Link to="/lobby" style={{ color: 'var(--bw-acid)' }}>QUEUE ONE UP</Link>.</div></Panel>
      )}

      {/* OPEN POSITIONS */}
      <Panel>
        <div className="bw-h3">OPEN POSITIONS · {wagers.length}</div>

        {loading && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING…</div>}
        {!loading && wagers.length === 0 && (
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO WAGERS YET.</div>
        )}
        <div className="bw-stack">
          {wagers.map(w => (
            <Link key={w.id} to={`/playback/${w.match_id}`} style={{
              display: 'block', padding: 10, background: 'var(--bw-bg)',
              boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
              textDecoration: 'none', color: 'inherit',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-yellow)' }}>
                    ◇ {w.amount_sol} SOL
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                    MATCH {w.match_id?.slice(0, 8)} · {w.created_at ? new Date(w.created_at).toLocaleDateString() : ''}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.08em', color: STATUS_COLORS[w.status] || 'var(--bw-ink)' }}>
                    {(w.status || '').toUpperCase()}
                    {w.status === 'placed' && (() => { const liveStatuses = pending.find(p => p.id === w.match_id); return liveStatuses ? <span className="blink"> ●</span> : null; })()}
                  </span>
                  {w.payout_sol > 0 && w.status === 'won' && (
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-acid)' }}>
                      +{(w.payout_sol - w.amount_sol).toFixed(2)} SOL
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </Panel>

      {/* SUMMARY */}
      {wagers.length > 0 && (
        <Panel>
          <div className="bw-h3">LIFETIME · {wagers.length} BETS</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
            <Stat label="WAGERED" value={`${stats.totalWagered.toFixed(2)} SOL`} color="var(--bw-ink)" />
            <Stat label="WON"      value={`${stats.won.toFixed(2)} SOL`}        color="var(--bw-acid)" />
            <Stat label="LOST"     value={`${stats.lost.toFixed(2)} SOL`}       color="var(--bw-blood)" />
            <Stat label="NET"      value={`${stats.net >= 0 ? '+' : ''}${stats.net.toFixed(2)} SOL`} color={stats.net >= 0 ? 'var(--bw-acid)' : 'var(--bw-blood)'} />
          </div>
        </Panel>
      )}
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ padding: 10, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}
