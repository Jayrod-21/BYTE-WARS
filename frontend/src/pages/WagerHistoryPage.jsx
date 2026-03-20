import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUserWagers, getUser } from '../services/api';

const STATUS_COLORS = {
  won: 'var(--success)',
  lost: 'var(--danger)',
  refunded: 'var(--warning)',
  locked: 'var(--accent)',
  placed: 'var(--text-dim)',
  cancelled: 'var(--text-dim)',
};

export default function WagerHistoryPage() {
  const [wagers, setWagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const user = getUser();

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    getUserWagers(user.id)
      .then(setWagers)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const totalWagered = wagers.reduce((sum, w) => sum + w.amount_sol, 0);
  const totalWon = wagers.filter(w => w.status === 'won').reduce((sum, w) => sum + w.payout_sol, 0);
  const totalLost = wagers.filter(w => w.status === 'lost').reduce((sum, w) => sum + w.amount_sol, 0);
  const netPnl = totalWon - totalLost;

  if (!user) {
    return (
      <div>
        <h1 className="page-title">Wager History</h1>
        <div className="card" style={{ textAlign: 'center' }}>
          <Link to="/login">Login</Link> to view your wager history.
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Wager History</h1>

      {error && <div className="error mb-12">{error}</div>}
      {loading && <div className="loading">Loading wagers...</div>}

      {/* Summary */}
      {!loading && wagers.length > 0 && (
        <div className="card mb-12" style={{ borderColor: 'var(--warning)' }}>
          <div className="stat-row">
            <span className="stat-label">Total Wagered</span>
            <span className="stat-value">{totalWagered.toFixed(4)} SOL</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Won</span>
            <span style={{ color: 'var(--success)' }}>{totalWon.toFixed(4)} SOL</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Lost</span>
            <span style={{ color: 'var(--danger)' }}>{totalLost.toFixed(4)} SOL</span>
          </div>
          <div className="stat-row" style={{ borderTop: '1px solid var(--border)', paddingTop: 4, marginTop: 4 }}>
            <span className="stat-label">Net P&L</span>
            <span style={{ color: netPnl >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 'bold' }}>
              {netPnl >= 0 ? '+' : ''}{netPnl.toFixed(4)} SOL
            </span>
          </div>
        </div>
      )}

      {/* Wager list */}
      {wagers.map(w => (
        <div key={w.id} className="card mb-12" style={{
          borderColor: STATUS_COLORS[w.status] || 'var(--border)',
        }}>
          <div className="flex flex-between flex-center">
            <strong>{w.amount_sol} SOL</strong>
            <span style={{
              color: STATUS_COLORS[w.status],
              textTransform: 'uppercase',
              fontSize: '0.8em',
              fontWeight: 'bold',
            }}>
              {w.status}
            </span>
          </div>
          <div className="stat-row mt-12">
            <span className="stat-label">Champion</span>
            <span className="stat-value" style={{ fontSize: '0.8em' }}>{w.champion_id.slice(0, 12)}...</span>
          </div>
          {w.payout_sol > 0 && (
            <div className="stat-row">
              <span className="stat-label">Payout</span>
              <span style={{ color: 'var(--success)' }}>{w.payout_sol.toFixed(4)} SOL</span>
            </div>
          )}
          <div className="flex flex-between mt-12" style={{ fontSize: '0.75em', color: 'var(--text-dim)' }}>
            <span>{new Date(w.created_at).toLocaleDateString()}</span>
            <Link to={`/playback/${w.match_id}`} style={{ color: 'var(--accent)' }}>
              Watch Match
            </Link>
          </div>
        </div>
      ))}

      {!loading && wagers.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          No wagers placed yet. Visit the <Link to="/lobby" style={{ color: 'var(--accent)' }}>Battle Lobby</Link> to place your first wager!
        </div>
      )}
    </div>
  );
}
