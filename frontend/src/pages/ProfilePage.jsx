import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMe, getWalletBalance, listChampions, getUserWagers } from '../services/api';
import { PixelButton, Pill, Panel, SolDiamond, Sprite } from '../ui/primitives';

export default function ProfilePage({ user }) {
  const [profile, setProfile] = useState(null);
  const [balance, setBalance] = useState(null);
  const [championCount, setChampionCount] = useState(0);
  const [wagerCount, setWagerCount] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    const wallet = user.wallet_address || `devnet_${user.id}`;
    Promise.all([
      getMe().catch(e => { setError(e.message); return null; }),
      getWalletBalance(wallet).catch(() => null),
      listChampions().catch(() => []),
      getUserWagers(user.id).catch(() => []),
    ]).then(([me, bal, champs, wagers]) => {
      setProfile(me);
      setBalance(bal?.balance_sol ?? bal?.balance ?? 0);
      setChampionCount(champs.length);
      setWagerCount(wagers.length);
    });
  }, [user]);

  if (!user) {
    return (
      <Panel>
        <h1 className="bw-h1">{'>'} PROFILE</h1>
        <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOG IN TO VIEW YOUR PROFILE.</div>
        <Link to="/login" style={{ display: 'inline-block', marginTop: 12 }}>
          <PixelButton variant="acid">LOG IN</PixelButton>
        </Link>
      </Panel>
    );
  }

  return (
    <div className="bw-stack-lg" style={{ maxWidth: 720, margin: '0 auto' }}>
      <h1 className="bw-h1">{'>'} PROFILE</h1>

      <Panel>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div style={{
            padding: 10,
            background: 'linear-gradient(180deg, rgba(182,255,60,0.2) 0%, transparent 80%)',
            boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line-2)',
          }}>
            <Sprite kind="knight" scale={4} glow="var(--bw-acid)" />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 14, color: 'var(--bw-acid)', letterSpacing: '0.05em' }}>
              {user.username?.toUpperCase()}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-low)', marginTop: 4 }}>
              ID · {user.id?.slice(0, 16)}…
            </div>
            {profile?.created_at && (
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-low)', marginTop: 2 }}>
                JOINED · {new Date(profile.created_at).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      </Panel>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
        <Stat label="BALANCE"   value={<><SolDiamond /> {balance == null ? '…' : Number(balance).toFixed(2)}</>} color="var(--bw-yellow)" />
        <Stat label="CHAMPIONS" value={championCount} color="var(--bw-acid)" />
        <Stat label="WAGERS"    value={wagerCount} color="var(--bw-magenta)" />
      </div>

      <Panel>
        <div className="bw-h3">WALLET</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink)', wordBreak: 'break-all' }}>
          {profile?.wallet_address || `devnet_${user.id}`}
        </div>
      </Panel>

      {error && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>}

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Link to="/wagers" style={{ textDecoration: 'none' }}><PixelButton variant="ghost">WAGER HISTORY</PixelButton></Link>
        <Link to="/history" style={{ textDecoration: 'none' }}><PixelButton variant="ghost">MATCH HISTORY</PixelButton></Link>
        <Link to="/clans" style={{ textDecoration: 'none' }}><PixelButton variant="ghost">MY CLAN</PixelButton></Link>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ padding: 12, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}
