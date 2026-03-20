import { useState, useEffect } from 'react';
import { getMe } from '../services/api';

export default function ProfilePage({ user }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      getMe()
        .then(setProfile)
        .catch(e => setError(e.message));
    }
  }, [user]);

  if (!user) {
    return (
      <div style={{ textAlign: 'center', marginTop: 60 }}>
        <h1 className="page-title">Profile</h1>
        <p style={{ color: 'var(--text-dim)' }}>Log in to view your profile.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 500, margin: '0 auto' }}>
      <h1 className="page-title">Profile</h1>
      <div className="card">
        <div className="stat-row">
          <span className="stat-label">Username</span>
          <span className="stat-value">{user.username}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">User ID</span>
          <span className="stat-value" style={{ fontSize: '0.75em' }}>{user.id}</span>
        </div>
        {profile && (
          <>
            <div className="stat-row">
              <span className="stat-label">Created</span>
              <span className="stat-value">
                {profile.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Wallet</span>
              <span className="stat-value">{profile.wallet_address || 'Not connected'}</span>
            </div>
          </>
        )}
        {error && <div className="error mt-12">{error}</div>}
      </div>
    </div>
  );
}
