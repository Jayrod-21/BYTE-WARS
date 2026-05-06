import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { PixelButton, Pill, Sprite, archetypeSprite, Panel } from '../ui/primitives';

// Demo seed — leaderboard / friends fixtures.
// In production these would come from /api/leaderboard, /api/friends, etc.
const FRIENDS = [
  { id: 'f1', name: 'NIGHT_VEX',     archetype: 'assassin', level: 28, w: 142, l: 56, status: 'online',   rank: 12 },
  { id: 'f2', name: 'IRONBARK_REX',  archetype: 'tank',     level: 31, w: 188, l: 72, status: 'in-match', rank: 7 },
  { id: 'f3', name: 'ZARA_MOONSHOT', archetype: 'ranger',   level: 24, w: 92,  l: 78, status: 'online',   rank: 41 },
  { id: 'f4', name: 'ECHO_PRIME',    archetype: 'mage',     level: 19, w: 41,  l: 39, status: 'offline',  rank: 256 },
  { id: 'f5', name: 'KAI_SCORCH',    archetype: 'mage',     level: 33, w: 271, l: 99, status: 'in-match', rank: 4 },
  { id: 'f6', name: 'PIXEL_MOM',     archetype: 'support',  level: 22, w: 73,  l: 81, status: 'offline',  rank: 178 },
  { id: 'f7', name: 'GHOST_RUNNER',  archetype: 'assassin', level: 35, w: 421, l: 188, status: 'online',  rank: 2 },
];

const STATUS_COLORS = {
  online:    'var(--bw-acid)',
  'in-match': 'var(--bw-magenta)',
  offline:   'var(--bw-ink-low)',
};

function winrate(w, l) { return w + l > 0 ? Math.round(w / (w + l) * 100) : 0; }
function rateColor(p) { return p >= 60 ? 'var(--bw-acid)' : p >= 45 ? 'var(--bw-yellow)' : 'var(--bw-blood)'; }

export default function SocialPage() {
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let xs = FRIENDS;
    if (tab === 'online') xs = xs.filter(f => f.status !== 'offline');
    if (tab === 'leaderboard') {
      xs = [...FRIENDS].filter(f => f.w + f.l >= 50)
        .sort((a, b) => winrate(b.w, b.l) - winrate(a.w, a.l) || b.w - a.w);
    }
    if (search) xs = xs.filter(f => f.name.toLowerCase().includes(search.toLowerCase()));
    return xs;
  }, [tab, search]);

  return (
    <div className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} SOCIAL</h1>

      <div style={{ display: 'flex', gap: 4 }}>
        <Tab active={tab === 'all'}        onClick={() => setTab('all')}>ALL · {FRIENDS.length}</Tab>
        <Tab active={tab === 'online'}     onClick={() => setTab('online')}>ONLINE · {FRIENDS.filter(f => f.status !== 'offline').length}</Tab>
        <Tab active={tab === 'leaderboard'} onClick={() => setTab('leaderboard')}>LEADERBOARD</Tab>
      </div>

      {tab === 'leaderboard' && (
        <div style={{ background: 'var(--bw-cyan)', color: '#001214', padding: '6px 10px', fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.05em' }}>
          SORTED BY: WIN RATE → TOTAL WINS · MIN 50 GAMES TO QUALIFY
        </div>
      )}

      <input
        type="search"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="search by callsign…"
        style={{ width: '100%' }}
      />

      <div className="bw-stack">
        {filtered.map((f, i) => (
          <Row key={f.id} friend={f} rank={i + 1} showRankBadge={tab === 'leaderboard'} />
        ))}
        {filtered.length === 0 && (
          <Panel><div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO RESULTS.</div></Panel>
        )}
      </div>

      <Panel>
        <div className="bw-h3">CLANS</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', marginBottom: 10 }}>
          BAND TOGETHER FOR WEEKLY QUESTS, TOURNAMENTS, AND TREASURY-FUNDED MATCHES.
        </div>
        <Link to="/clans" style={{ textDecoration: 'none' }}>
          <PixelButton variant="cyan">{'>>'} VIEW MY CLAN</PixelButton>
        </Link>
      </Panel>
    </div>
  );
}

function Row({ friend, rank, showRankBadge }) {
  const wr = winrate(friend.w, friend.l);
  const rankBadgeColor = rank === 1 ? 'var(--bw-yellow)' : rank === 2 ? 'var(--bw-cyan)' : rank === 3 ? 'var(--bw-magenta)' : 'var(--bw-line-2)';

  return (
    <div style={{
      padding: 10,
      background: 'var(--bw-bg-2)',
      boxShadow: 'inset -2px -2px 0 0 #000, inset 2px 2px 0 0 var(--bw-line-2), 0 4px 0 0 #000',
      display: 'flex', gap: 10, alignItems: 'center',
    }}>
      {showRankBadge && (
        <div style={{
          width: 36, height: 36,
          background: rankBadgeColor,
          color: '#000',
          fontFamily: 'var(--font-pixel)', fontSize: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: 'inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.4)',
        }}>
          #{rank}
        </div>
      )}

      <div style={{ position: 'relative' }}>
        <Sprite kind={archetypeSprite(friend.archetype)} scale={2} />
        <span style={{
          position: 'absolute', bottom: -2, right: -2,
          width: 10, height: 10,
          background: STATUS_COLORS[friend.status],
          boxShadow: '0 0 0 2px var(--bw-bg-2)',
        }}
        className={friend.status === 'in-match' ? 'blink' : ''}
        />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, letterSpacing: '0.05em', color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {friend.name}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
          LV.{friend.level} · {friend.w}W / {friend.l}L · <span style={{ color: rateColor(wr), fontWeight: 800 }}>{wr}%</span>
          <span style={{ color: 'var(--bw-ink-low)' }}> · GLOBAL #{friend.rank}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 4 }}>
        {friend.status === 'online' && (
          <PixelButton variant="acid" style={{ padding: '6px 8px', fontSize: 8 }} title="Duel">⚔ DUEL</PixelButton>
        )}
        {friend.status === 'in-match' && (
          <PixelButton variant="magenta" style={{ padding: '6px 8px', fontSize: 8 }} title="Watch">👁 WATCH</PixelButton>
        )}
        <PixelButton variant="ghost" style={{ padding: '6px 8px', fontSize: 8 }} title="Message">💬</PixelButton>
      </div>
    </div>
  );
}

function Tab({ active, onClick, children }) {
  return (
    <button type="button" onClick={onClick} style={{
      all: 'unset', cursor: 'pointer',
      padding: '8px 12px',
      fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.08em',
      color: active ? 'var(--bw-acid)' : 'var(--bw-ink-low)',
      borderBottom: active ? '3px solid var(--bw-acid)' : '3px solid transparent',
    }}>{children}</button>
  );
}
