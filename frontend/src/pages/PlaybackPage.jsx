import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPlayback, getPlaybackUrl } from '../services/api';

export default function PlaybackPage() {
  const { matchId } = useParams();
  const [playback, setPlayback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('embedded'); // embedded or data

  useEffect(() => {
    getPlayback(matchId)
      .then(setPlayback)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [matchId]);

  if (loading) return <div className="loading">Loading playback...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!playback) return null;

  return (
    <div>
      <div className="flex flex-between flex-center mb-12">
        <h1 className="page-title" style={{ marginBottom: 0 }}>Match Playback</h1>
        <div className="flex gap-8">
          <button
            className={`btn btn-sm ${viewMode === 'embedded' ? '' : ''}`}
            onClick={() => setViewMode(viewMode === 'embedded' ? 'data' : 'embedded')}
          >
            {viewMode === 'embedded' ? 'Show Stats' : 'Show Viewer'}
          </button>
          <Link to="/history" className="btn btn-sm">Back</Link>
        </div>
      </div>

      {viewMode === 'embedded' ? (
        <iframe
          src={getPlaybackUrl(matchId)}
          style={{
            width: '100%',
            height: '700px',
            border: '1px solid var(--border)',
            borderRadius: 6,
            background: '#0a0a1a',
          }}
          title="Match Playback"
        />
      ) : (
        <div>
          {/* Match info */}
          <div className="card">
            <div className="flex flex-between flex-center">
              <strong>
                {playback.status === 'complete' && playback.winner_name
                  ? `Winner: ${playback.winner_name}`
                  : `Status: ${playback.status}`}
              </strong>
              <span className={`status status-${playback.status}`}>{playback.status}</span>
            </div>
            <div className="stat-row mt-12">
              <span className="stat-label">Total Turns</span>
              <span className="stat-value">{playback.total_turns}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Events</span>
              <span className="stat-value">{playback.events.length}</span>
            </div>
          </div>

          {/* Champion stats */}
          <h2 style={{ color: 'var(--accent)', fontSize: '1.1em', margin: '16px 0 8px' }}>Champion Stats</h2>
          <div className="grid grid-2">
            {Object.entries(playback.summary).map(([id, stats]) => (
              <div key={id} className="card" style={{
                borderColor: id === playback.winner_id ? 'var(--success)' : undefined,
              }}>
                <strong>
                  {stats.name}
                  {id === playback.winner_id ? ' (Winner)' : ''}
                </strong>
                <div className="stat-row mt-12">
                  <span className="stat-label">Damage Dealt</span>
                  <span className="stat-value">{Math.round(stats.damage_dealt)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Damage Taken</span>
                  <span style={{ color: 'var(--danger)' }}>{Math.round(stats.damage_taken)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Healing Done</span>
                  <span style={{ color: 'var(--success)' }}>{Math.round(stats.healing_done)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Kills</span>
                  <span className="stat-value">{stats.kills}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Actions</span>
                  <span className="stat-value">{stats.actions_taken}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
