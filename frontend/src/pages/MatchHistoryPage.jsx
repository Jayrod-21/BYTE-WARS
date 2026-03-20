import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listMatches } from '../services/api';

export default function MatchHistoryPage() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listMatches()
      .then(data => setMatches(data.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-title">Match History</h1>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading matches...</div>}

      {!loading && matches.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          No matches yet. <Link to="/lobby" style={{ color: 'var(--accent)' }}>Start a battle</Link>
        </div>
      )}

      {matches.map(match => (
        <div key={match.id} className="card">
          <div className="flex flex-between flex-center">
            <div>
              <strong>{match.champion_names.join(' vs ')}</strong>
              <div style={{ fontSize: '0.8em', color: 'var(--text-dim)', marginTop: 4 }}>
                {match.total_turns} turns
                {match.created_at && ` | ${new Date(match.created_at).toLocaleString()}`}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className={`status status-${match.status}`}>{match.status}</span>
              {match.winner_name && (
                <div style={{ fontSize: '0.85em', color: 'var(--success)', marginTop: 4 }}>
                  Winner: {match.winner_name}
                </div>
              )}
            </div>
          </div>
          {match.status === 'complete' || match.status === 'timed_out' ? (
            <div className="mt-12">
              <Link to={`/playback/${match.id}`} className="btn btn-sm">Watch Playback</Link>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
