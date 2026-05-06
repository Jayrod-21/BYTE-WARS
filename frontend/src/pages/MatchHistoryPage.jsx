import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listMatches } from '../services/api';
import { PixelButton, Pill, Panel, Sprite, archetypeSprite } from '../ui/primitives';

const STATUS_COLORS = {
  complete:  'var(--bw-acid)',
  timed_out: 'var(--bw-yellow)',
  pending:   'var(--bw-cyan)',
  created:   'var(--bw-cyan)',
  failed:    'var(--bw-blood)',
};

export default function MatchHistoryPage() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listMatches()
      .then(data => setMatches((data || []).sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} HISTORY · {matches.length}</h1>

      {error && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>}
      {loading && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING…</div>}

      {!loading && matches.length === 0 && (
        <Panel>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>
            NO MATCHES YET. <Link to="/lobby" style={{ color: 'var(--bw-acid)' }}>QUEUE UP →</Link>
          </div>
        </Panel>
      )}

      <div className="bw-stack">
        {matches.map(m => {
          const playable = m.status === 'complete' || m.status === 'timed_out';
          return (
            <div key={m.id} style={{
              padding: 12,
              background: 'var(--bw-bg-2)',
              boxShadow: m.status === 'complete'
                ? 'inset -2px -2px 0 0 #000, inset 2px 2px 0 0 var(--bw-line-2), 0 4px 0 0 #000'
                : 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
              borderLeft: `4px solid ${STATUS_COLORS[m.status] || 'var(--bw-line)'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-ink)', letterSpacing: '0.05em', marginBottom: 4 }}>
                    {(m.champion_names || []).join(' VS ').toUpperCase()}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
                    {m.total_turns || 0} TURNS · {m.created_at ? new Date(m.created_at).toLocaleString() : ''}
                  </div>
                  {m.winner_name && (
                    <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: 'var(--bw-yellow)', letterSpacing: '0.06em', marginTop: 6 }}>
                      ★ {m.winner_name.toUpperCase()}
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                  <Pill color={STATUS_COLORS[m.status] || 'var(--bw-line)'}>{m.status}</Pill>
                  {playable && (
                    <Link to={`/playback/${m.id}`} style={{ textDecoration: 'none' }}>
                      <PixelButton variant="acid" style={{ padding: '6px 10px', fontSize: 8 }}>WATCH ▶</PixelButton>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
