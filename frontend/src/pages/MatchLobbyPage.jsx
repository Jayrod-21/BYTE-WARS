import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listChampions, createMatch, startMatch } from '../services/api';

export default function MatchLobbyPage() {
  const navigate = useNavigate();
  const [champions, setChampions] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fighting, setFighting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listChampions().then(setChampions).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);

  function toggleSelect(id) {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev
    );
  }

  async function handleFight() {
    if (selected.length < 2) { setError('Select at least 2 champions'); return; }
    setError('');
    setFighting(true);
    try {
      const match = await createMatch(selected);
      const result = await startMatch(match.id);
      navigate(`/playback/${match.id}`);
    } catch (err) {
      setError(err.message);
      setFighting(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Battle Lobby</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: 16 }}>
        Select 2-4 champions for a free-for-all battle.
      </p>

      {error && <div className="error mb-12">{error}</div>}
      {loading && <div className="loading">Loading champions...</div>}

      <div className="grid grid-2">
        {champions.map(champ => {
          const isSelected = selected.includes(champ.id);
          return (
            <div
              key={champ.id}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? 'var(--accent)' : undefined,
                background: isSelected ? 'var(--bg-input)' : undefined,
              }}
              onClick={() => toggleSelect(champ.id)}
            >
              <div className="flex flex-between flex-center">
                <strong>{champ.name}</strong>
                <span className={`badge badge-${champ.archetype}`}>{champ.archetype}</span>
              </div>
              <div className="stat-row mt-12">
                <span className="stat-label">HP:{champ.stats.health} STR:{champ.stats.strength} END:{champ.stats.endurance}</span>
                <span className="stat-value">{isSelected ? 'SELECTED' : ''}</span>
              </div>
            </div>
          );
        })}
      </div>

      {champions.length > 0 && (
        <div className="mt-12">
          <button
            className="btn"
            onClick={handleFight}
            disabled={selected.length < 2 || fighting}
            style={{ width: '100%', padding: '12px 20px', fontSize: '1.1em' }}
          >
            {fighting ? 'Fighting...' : `Fight! (${selected.length} champions)`}
          </button>
        </div>
      )}
    </div>
  );
}
