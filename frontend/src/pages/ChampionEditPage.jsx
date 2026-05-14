import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getChampion, updateChampion } from '../services/api';
import { PixelButton, Pill, Sprite, archetypeSprite, Panel } from '../ui/primitives';

const MODELS = [
  'claude-sonnet-4-6',
  'claude-haiku-4-5-20251001',
  'gpt-4o',
  'gpt-4o-mini',
  'gemini-pro',
];

export default function ChampionEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [champion, setChampion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [clearKey, setClearKey] = useState(false);
  const [model, setModel] = useState(MODELS[0]);

  useEffect(() => {
    let cancelled = false;
    getChampion(id)
      .then(c => {
        if (cancelled) return;
        setChampion(c);
        setSystemPrompt(c.system_prompt || '');
        setModel(c.model || MODELS[0]);
      })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { system_prompt: systemPrompt, model };
      if (apiKey) payload.api_key = apiKey;
      else if (clearKey) payload.api_key = '';
      await updateChampion(id, payload);
      navigate('/champions');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING…</div>;
  }
  if (!champion) {
    return <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error || 'Champion not found'}</div>;
  }

  return (
    <form onSubmit={handleSave} className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} EDIT / {champion.name.toUpperCase()}</h1>

      <Panel style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Sprite kind={archetypeSprite(champion.archetype)} scale={5} />
        <div>
          <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 12, color: 'var(--bw-acid)' }}>
            {champion.name.toUpperCase()}
          </div>
          <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Pill color="var(--bw-cyan)">{champion.archetype}</Pill>
            <Pill color={champion.has_api_key ? 'var(--bw-acid)' : 'var(--bw-line-2)'} textColor={champion.has_api_key ? '#0a1a00' : 'var(--bw-ink-dim)'}>
              {champion.has_api_key ? 'KEY ✓' : 'NO KEY · MOCKBOT'}
            </Pill>
          </div>
        </div>
      </Panel>

      <Panel>
        <div className="bw-h3">SYSTEM PROMPT</div>
        <textarea
          rows={5}
          value={systemPrompt}
          onChange={e => setSystemPrompt(e.target.value)}
          maxLength={5000}
          style={{ width: '100%', fontFamily: 'var(--font-mono)', color: 'var(--bw-acid)' }}
        />
      </Panel>

      <Panel>
        <div className="bw-h3">AI MODEL</div>
        <select value={model} onChange={e => setModel(e.target.value)} style={{ width: '100%' }}>
          {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </Panel>

      <Panel>
        <div className="bw-h3">API KEY · {champion.has_api_key ? 'CURRENTLY SET' : 'NOT SET'}</div>
        <input
          type="password"
          value={apiKey}
          onChange={e => { setApiKey(e.target.value); if (e.target.value) setClearKey(false); }}
          placeholder={champion.has_api_key ? '••• leave blank to keep •••' : 'sk-… or your provider key'}
          autoComplete="off"
          style={{ width: '100%' }}
        />
        {champion.has_api_key && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)' }}>
            <input type="checkbox" checked={clearKey} onChange={e => { setClearKey(e.target.checked); if (e.target.checked) setApiKey(''); }} />
            Remove existing key (fall back to mockbot)
          </label>
        )}
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-low)', marginTop: 6 }}>
          ENCRYPTED AT REST · NO KEY = MOCKBOT (RANDOM ACTIONS)
        </div>
      </Panel>

      {error && (
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-blood)',
          padding: '8px 10px', background: 'rgba(255,60,92,0.08)',
          boxShadow: 'inset 0 0 0 2px var(--bw-blood)',
        }}>! {error}</div>
      )}

      <div style={{ display: 'flex', gap: 12, paddingBottom: 24 }}>
        <PixelButton variant="ghost" type="button" onClick={() => navigate('/champions')}>CANCEL</PixelButton>
        <PixelButton variant="acid" type="submit" full disabled={saving}>
          {saving ? 'SAVING…' : 'SAVE'}
        </PixelButton>
      </div>
    </form>
  );
}
