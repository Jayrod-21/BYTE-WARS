import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listChampions } from '../services/api';

export default function ChampionsPage() {
  const [champions, setChampions] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { load(); }, [filter]);

  async function load() {
    setLoading(true);
    try {
      const data = await listChampions(filter || undefined);
      setChampions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="flex flex-between flex-center mb-12">
        <h1 className="page-title" style={{ marginBottom: 0 }}>Champions</h1>
        <Link to="/champions/new" className="btn">+ New Champion</Link>
      </div>

      <div className="flex gap-8 mb-12">
        <button className={`btn btn-sm ${!filter ? 'active' : ''}`} onClick={() => setFilter('')}>All</button>
        {['tank', 'assassin', 'mage', 'ranger', 'support'].map(arch => (
          <button
            key={arch}
            className={`btn btn-sm ${filter === arch ? 'active' : ''}`}
            onClick={() => setFilter(filter === arch ? '' : arch)}
          >
            {arch}
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading champions...</div>}

      {!loading && champions.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          No champions yet. <Link to="/champions/new" style={{ color: 'var(--accent)' }}>Create one</Link>
        </div>
      )}

      <div className="grid grid-2">
        {champions.map(champ => (
          <div key={champ.id} className="card">
            <div className="flex flex-between flex-center">
              <strong>{champ.name}</strong>
              <span className={`badge badge-${champ.archetype}`}>{champ.archetype}</span>
            </div>
            <div className="stat-row mt-12">
              <span className="stat-label">HP</span>
              <span className="stat-value">{champ.stats.health}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">STR</span>
              <span className="stat-value">{champ.stats.strength}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">END</span>
              <span className="stat-value">{champ.stats.endurance}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Gear</span>
              <span className="stat-value">{champ.gear_slots.length + champ.base_gear.length} items</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">AI Model</span>
              <span className="stat-value">{champ.model || 'default'}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">API Key</span>
              <span className="stat-value">{champ.has_api_key ? 'Set' : 'Not set'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
