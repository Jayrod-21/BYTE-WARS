import { useState } from 'react';
import {
  PixelButton, Pill, Sprite, archetypeSprite, Panel, SolDiamond,
} from '../ui/primitives';

const CLAN = {
  tag: 'NEONFIST',
  name: 'NEON FIST CONSORTIUM',
  motto: 'we don\'t lose, we recompile.',
  worldRank: 14,
  rating: 2841,
  treasury: 312.4,
  wins: 91, losses: 22,
  color: 'var(--bw-magenta)',
};

const QUESTS = [
  { id: 'q1', label: 'WIN 10 RANKED MATCHES',     progress: 7, target: 10, reward: '◇ 5 SOL' },
  { id: 'q2', label: 'DEAL 50K DAMAGE COLLECTIVE', progress: 32, target: 50, reward: '◇ 8 SOL' },
  { id: 'q3', label: 'FORGE 3 NEW CHAMPIONS',     progress: 1,  target: 3,  reward: '◇ 2 SOL + GEAR CHEST' },
];

const MEMBERS_SEED = [
  { id: 'm1', name: 'NIGHT_VEX',     archetype: 'assassin', role: 'captain', rank: 12,  contrib: 482, isYou: false },
  { id: 'm2', name: 'IRONBARK_REX',  archetype: 'tank',     role: 'officer', rank: 7,   contrib: 391, isYou: false },
  { id: 'm3', name: 'ZARA_MOONSHOT', archetype: 'ranger',   role: 'member',  rank: 41,  contrib: 268, isYou: false },
  { id: 'm4', name: 'YOU',           archetype: 'mage',     role: 'member',  rank: 178, contrib: 142, isYou: true },
  { id: 'm5', name: 'KAI_SCORCH',    archetype: 'mage',     role: 'member',  rank: 4,   contrib: 510, isYou: false },
  { id: 'm6', name: 'PIXEL_MOM',     archetype: 'support',  role: 'member',  rank: 178, contrib: 88,  isYou: false },
  { id: 'm7', name: 'GHOST_RUNNER',  archetype: 'assassin', role: 'member',  rank: 2,   contrib: 712, isYou: false },
];

const ROLE_COLORS = {
  captain: 'var(--bw-yellow)',
  officer: 'var(--bw-magenta)',
  member:  'var(--bw-line-2)',
};

const REQUESTS_SEED = [
  { id: 'r1', name: 'BYTE_BANDIT', rank: 312, level: 18, message: 'looking to climb. mage main, gpt-4o.' },
  { id: 'r2', name: 'SPECTRE_M3',  rank: 88,  level: 27, message: 'ex-ironclad. bring solid trade pipeline.' },
  { id: 'r3', name: 'HEXLOOP',     rank: 401, level: 12, message: 'new fighter. eager to grind quests.' },
];

const POLL = {
  question: 'PICK SAT TOURNAMENT',
  closes: 'closes 18h',
  options: [
    { id: 'o1', label: 'ACID RAIN INVITATIONAL', prize: '◇ 25 SOL', votes: 12 },
    { id: 'o2', label: 'CRYO DUEL CIRCUIT',      prize: '◇ 18 SOL', votes: 8 },
    { id: 'o3', label: 'PIXEL CUP S5',           prize: '◇ 40 SOL', votes: 19 },
    { id: 'o4', label: 'NEON CLASH',             prize: '◇ 12 SOL', votes: 5 },
  ],
};

const CHAT_SEED = [
  { user: 'KAI_SCORCH',    text: 'gz on the run kai',         time: '14:32' },
  { user: 'NIGHT_VEX',     text: 'who\'s in for tournament sat?', time: '14:35' },
  { user: 'IRONBARK_REX',  text: 'pick 3, prize is biggest',  time: '14:36' },
  { user: 'ZARA_MOONSHOT', text: 'new bow drop in shop is nuts', time: '14:40' },
];

export default function ClansPage() {
  const [viewerRole, setViewerRole] = useState('member');
  const [members, setMembers] = useState(MEMBERS_SEED);
  const [requests, setRequests] = useState(REQUESTS_SEED);
  const [pollVotes, setPollVotes] = useState(Object.fromEntries(POLL.options.map(o => [o.id, o.votes])));
  const [pollVote, setPollVote] = useState(null);
  const [pollLocked, setPollLocked] = useState(false);
  const [rosterOpen, setRosterOpen] = useState(false);
  const [requestsOpen, setRequestsOpen] = useState(false);
  const [chat, setChat] = useState(CHAT_SEED);
  const [chatInput, setChatInput] = useState('');

  const totalVotes = Object.values(pollVotes).reduce((s, v) => s + v, 0);
  const winningId = Object.entries(pollVotes).sort((a, b) => b[1] - a[1])[0]?.[0];

  function castVote(optionId) {
    if (pollLocked) return;
    setPollVotes(prev => {
      const next = { ...prev };
      if (pollVote && pollVote !== optionId) next[pollVote] = Math.max(0, (next[pollVote] || 0) - 1);
      if (pollVote !== optionId) next[optionId] = (next[optionId] || 0) + 1;
      return next;
    });
    setPollVote(optionId);
  }

  function sendChat() {
    if (!chatInput.trim()) return;
    setChat(prev => [...prev, { user: 'YOU', text: chatInput.trim(), time: new Date().toTimeString().slice(0, 5) }]);
    setChatInput('');
  }

  function kickMember(id) {
    setMembers(prev => prev.filter(m => m.id !== id));
  }

  function acceptRequest(req) {
    setRequests(prev => prev.filter(r => r.id !== req.id));
    setMembers(prev => [...prev, { id: req.id, name: req.name, archetype: 'mage', role: 'member', rank: req.rank, contrib: 0, isYou: false }]);
  }
  function denyRequest(id) {
    setRequests(prev => prev.filter(r => r.id !== id));
  }

  return (
    <div className="bw-stack-lg">
      {/* BANNER */}
      <Panel style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
        <div style={{
          padding: 20,
          background: `linear-gradient(135deg, ${CLAN.color}66 0%, transparent 70%), repeating-linear-gradient(45deg, #2a0a22 0 12px, #1a0a14 12px 24px)`,
          position: 'relative',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 18, color: CLAN.color, letterSpacing: '0.08em', textShadow: '3px 3px 0 #000' }}>
                [{CLAN.tag}]
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, color: 'var(--bw-ink)', marginTop: 4, fontWeight: 800 }}>
                {CLAN.name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', marginTop: 4, fontStyle: 'italic' }}>
                "{CLAN.motto}"
              </div>
            </div>
            <button type="button" onClick={() => setViewerRole(viewerRole === 'captain' ? 'member' : 'captain')}
              aria-label={`Toggle clan viewer role; currently ${viewerRole}`}
              aria-pressed={viewerRole === 'captain'}
              style={{
                all: 'unset', cursor: 'pointer',
                padding: '6px 10px',
                fontFamily: 'var(--font-pixel)', fontSize: 7, letterSpacing: '0.08em',
                background: viewerRole === 'captain' ? 'var(--bw-yellow)' : 'var(--bw-line-2)',
                color: viewerRole === 'captain' ? '#1a1400' : 'var(--bw-ink)',
                boxShadow: 'inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.3)',
              }}>
              {viewerRole === 'captain' ? <><span aria-hidden="true">👑</span>{' '}CAPTAIN VIEW</> : 'MEMBER VIEW'}
            </button>
          </div>
        </div>

        {/* KPI strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', borderTop: '2px solid var(--bw-line)' }}>
          <Kpi label="MEMBERS" value={`${members.length}/50`} color="var(--bw-cyan)" />
          <Kpi label="RATING" value={CLAN.rating} color="var(--bw-acid)" />
          <Kpi label="TREASURY" value={<><SolDiamond /> {CLAN.treasury}</>} color="var(--bw-yellow)" />
          <Kpi label="W/L" value={`${CLAN.wins}/${CLAN.losses}`} color="var(--bw-magenta)" />
          <Kpi label="WORLD RANK" value={`#${CLAN.worldRank}`} color="var(--bw-blood)" />
        </div>
      </Panel>

      <div className="bw-split">
        {/* LEFT */}
        <div className="bw-stack-lg">
          {/* QUESTS */}
          <Panel>
            <div className="bw-h3">WEEKLY QUESTS</div>
            <div className="bw-stack">
              {QUESTS.map(q => (
                <div key={q.id} style={{ padding: 10, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink)' }}>{q.label}</span>
                    <Pill color="var(--bw-yellow)">{q.reward}</Pill>
                  </div>
                  <div style={{ height: 10, background: '#000', boxShadow: 'inset 0 0 0 2px var(--bw-line)' }}>
                    <div style={{ width: `${(q.progress / q.target) * 100}%`, height: '100%', background: 'var(--bw-acid)' }} />
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)', marginTop: 4 }}>
                    {q.progress}/{q.target}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* MEMBERS */}
          <Panel>
            <button type="button" onClick={() => setRosterOpen(o => !o)}
              aria-expanded={rosterOpen}
              aria-controls="clan-members-list"
              style={{
              all: 'unset', cursor: 'pointer', width: '100%',
              display: 'flex', justifyContent: 'space-between',
              fontFamily: 'var(--font-pixel)', fontSize: 9, letterSpacing: '0.08em', color: 'var(--bw-ink)',
            }}>
              <span>👥 MEMBERS · {members.length}/50</span>
              <span style={{ color: 'var(--bw-cyan)' }}>{rosterOpen ? '▾ COLLAPSE' : '▸ EXPAND'}</span>
            </button>
            {rosterOpen && (
              <div id="clan-members-list" style={{ marginTop: 10 }} className="bw-stack">
                {members.map(m => (
                  <div key={m.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: 8,
                    background: m.isYou ? 'rgba(60,240,255,0.1)' : 'var(--bw-bg)',
                    boxShadow: m.isYou
                      ? 'inset 0 0 0 2px var(--bw-cyan)'
                      : 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
                  }}>
                    <Sprite kind={archetypeSprite(m.archetype)} scale={1.5} />
                    <Pill color={ROLE_COLORS[m.role]}>{m.role}</Pill>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: 'var(--bw-ink)' }}>{m.name}</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                        #{m.rank} · {m.contrib} CONTRIB
                      </div>
                    </div>
                    {viewerRole === 'captain' && !m.isYou && m.role !== 'captain' && (
                      <div style={{ display: 'flex', gap: 4 }}>
                        <PixelButton variant="ghost" style={{ padding: '4px 8px', fontSize: 7 }} onClick={() => kickMember(m.id)}>KICK</PixelButton>
                        <PixelButton variant="blood" style={{ padding: '4px 8px', fontSize: 7 }} onClick={() => kickMember(m.id)}>BAN</PixelButton>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Panel>

          {/* JOIN REQUESTS */}
          {viewerRole === 'captain' && (
            <Panel>
              <button type="button" onClick={() => setRequestsOpen(o => !o)}
                aria-expanded={requestsOpen}
                aria-controls="clan-join-requests"
                style={{
                all: 'unset', cursor: 'pointer', width: '100%',
                display: 'flex', justifyContent: 'space-between',
                fontFamily: 'var(--font-pixel)', fontSize: 9, letterSpacing: '0.08em', color: 'var(--bw-ink)',
              }}>
                <span>✉ JOIN REQUESTS {requests.length > 0 && <span className="blink" style={{ color: 'var(--bw-magenta)' }}>● {requests.length}</span>}</span>
                <span style={{ color: 'var(--bw-cyan)' }}>{requestsOpen ? '▾' : '▸'}</span>
              </button>
              {requestsOpen && (
                <div id="clan-join-requests" style={{ marginTop: 10 }} className="bw-stack">
                  {requests.length === 0 && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO PENDING REQUESTS.</div>}
                  {requests.map(r => (
                    <div key={r.id} style={{ padding: 10, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-ink)' }}>{r.name}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>LV.{r.level} · #{r.rank}</span>
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', fontStyle: 'italic', marginBottom: 8 }}>
                        "{r.message}"
                      </div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <PixelButton variant="acid" style={{ padding: '6px 10px', fontSize: 8 }} onClick={() => acceptRequest(r)}>✓ ACCEPT</PixelButton>
                        <PixelButton variant="blood" style={{ padding: '6px 10px', fontSize: 8 }} onClick={() => denyRequest(r.id)}>✕ DENY</PixelButton>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          )}

          {/* TOURNAMENT POLL */}
          <Panel>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <div className="bw-h3" style={{ marginBottom: 0 }}>{POLL.question}</div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-yellow)' }}>{POLL.closes}</span>
            </div>
            <div className="bw-stack">
              {POLL.options.map(o => {
                const v = pollVotes[o.id] || 0;
                const pct = totalVotes > 0 ? Math.round(v / totalVotes * 100) : 0;
                const isMine = pollVote === o.id;
                const isWinning = winningId === o.id;
                return (
                  <button type="button" key={o.id} onClick={() => castVote(o.id)} disabled={pollLocked}
                    style={{
                      all: 'unset', cursor: pollLocked ? 'default' : 'pointer',
                      padding: 10,
                      background: 'var(--bw-bg)',
                      boxShadow: isMine
                        ? 'inset 0 0 0 2px var(--bw-acid)'
                        : isWinning
                          ? 'inset 0 0 0 2px var(--bw-yellow)'
                          : 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
                      position: 'relative', overflow: 'hidden',
                    }}
                  >
                    <div style={{ position: 'absolute', inset: 0, width: `${pct}%`, background: isMine ? 'rgba(182,255,60,0.1)' : 'rgba(60,240,255,0.06)' }} />
                    <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-ink)', letterSpacing: '0.05em' }}>
                          {o.label} {isMine && <span style={{ color: 'var(--bw-acid)' }}>✓</span>}
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-yellow)', marginTop: 2 }}>{o.prize}</div>
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--bw-ink)', fontWeight: 800 }}>
                        {pct}% · {v}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
            {viewerRole === 'captain' && !pollLocked && (
              <div style={{ marginTop: 12 }}>
                <PixelButton variant="acid" full onClick={() => setPollLocked(true)}>👑 LOCK WINNER · ENTER CLAN</PixelButton>
              </div>
            )}
            {pollLocked && (
              <div style={{ marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-acid)' }}>
                ✓ ENTERED INTO {POLL.options.find(o => o.id === winningId)?.label}
              </div>
            )}
          </Panel>
        </div>

        {/* RIGHT — SHOUTBOX */}
        <Panel style={{ position: 'sticky', top: 80 }}>
          <div className="bw-h3">SHOUTBOX</div>
          <div className="panel-sunken" style={{ padding: 10, height: 380, overflowY: 'auto', background: '#000' }}>
            {chat.map((msg, i) => (
              <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, marginBottom: 6, lineHeight: 1.5 }}>
                <span style={{ color: 'var(--bw-ink-low)' }}>[{msg.time}]</span>
                <span style={{ color: msg.user === 'YOU' ? 'var(--bw-acid)' : 'var(--bw-cyan)', fontWeight: 800, margin: '0 6px' }}>
                  {msg.user}
                </span>
                <span style={{ color: 'var(--bw-ink)' }}>{msg.text}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
            <input type="text" value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendChat()}
              placeholder="say something…"
              style={{ flex: 1 }} />
            <PixelButton variant="acid" onClick={sendChat}>SEND</PixelButton>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Kpi({ label, value, color }) {
  return (
    <div style={{
      padding: 10, textAlign: 'center',
      borderRight: '2px solid var(--bw-line)',
      background: 'var(--bw-panel)',
    }}>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}
