import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createChampion } from '../services/api';

const ARCHETYPES = [
  { name: 'tank', desc: 'High durability, outlasts opponents', stats: 'HP:150 STR:35 END:75' },
  { name: 'assassin', desc: 'Fast and deadly, low survivability', stats: 'HP:80 STR:80 END:40' },
  { name: 'mage', desc: 'Raw power, glass cannon', stats: 'HP:90 STR:90 END:25' },
  { name: 'ranger', desc: 'Balanced, adaptable', stats: 'HP:110 STR:55 END:55' },
  { name: 'support', desc: 'Survival specialist, heals and endures', stats: 'HP:120 STR:30 END:70' },
];

export default function ChampionBuilderPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [archetype, setArchetype] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('claude-sonnet-4-6');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!archetype) { setError('Select an archetype'); return; }
    setError('');
    setLoading(true);
    try {
      await createChampion({
        name,
        archetype,
        system_prompt: systemPrompt,
        api_key: apiKey || undefined,
        model,
      });
      navigate('/champions');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Champion Builder</h1>
      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="form-group">
            <label>Champion Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Enter champion name"
              required
              maxLength={100}
            />
          </div>

          <div className="form-group">
            <label>Archetype</label>
            <div className="grid grid-3" style={{ marginTop: 6 }}>
              {ARCHETYPES.map(arch => (
                <div
                  key={arch.name}
                  className="card"
                  style={{
                    cursor: 'pointer',
                    borderColor: archetype === arch.name ? 'var(--accent)' : undefined,
                    background: archetype === arch.name ? 'var(--bg-input)' : undefined,
                  }}
                  onClick={() => setArchetype(arch.name)}
                >
                  <div className="flex flex-between flex-center">
                    <strong style={{ textTransform: 'capitalize' }}>{arch.name}</strong>
                    <span className={`badge badge-${arch.name}`}>{arch.name}</span>
                  </div>
                  <div style={{ fontSize: '0.8em', color: 'var(--text-dim)', marginTop: 4 }}>
                    {arch.desc}
                  </div>
                  <div style={{ fontSize: '0.75em', color: 'var(--accent)', marginTop: 4 }}>
                    {arch.stats}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="form-group">
            <label>System Prompt (Strategy / Personality)</label>
            <textarea
              value={systemPrompt}
              onChange={e => setSystemPrompt(e.target.value)}
              placeholder="Tell your champion how to fight. E.g.: 'Focus on healing when HP is low. Target the weakest opponent. Use power_surge when you have 3 AP.'"
              maxLength={5000}
            />
          </div>
        </div>

        <div className="card">
          <div className="form-group">
            <label>AI Model</label>
            <select value={model} onChange={e => setModel(e.target.value)}>
              <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
              <option value="claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gemini-pro">Gemini Pro</option>
            </select>
          </div>

          <div className="form-group">
            <label>API Key (optional — encrypted at rest)</label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="sk-... or your provider's API key"
            />
            <div style={{ fontSize: '0.75em', color: 'var(--text-dim)', marginTop: 4 }}>
              Without an API key, your champion uses random actions (MockBot).
            </div>
          </div>
        </div>

        {error && <div className="error mb-12">{error}</div>}

        <div className="flex gap-8">
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Creating...' : 'Create Champion'}
          </button>
          <button type="button" className="btn btn-danger" onClick={() => navigate('/champions')}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
