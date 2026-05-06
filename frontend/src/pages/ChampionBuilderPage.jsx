import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { createChampion } from '../services/api';
import {
  PixelButton, Pill, Sprite, archetypeSprite, Slot, ItemIcon, Panel,
} from '../ui/primitives';

const ARCHETYPES = [
  { name: 'tank',     desc: 'High durability, outlasts opponents',   base: { health: 150, strength: 35, endurance: 75 }, color: 'var(--bw-acid)' },
  { name: 'assassin', desc: 'Fast and deadly, low survivability',     base: { health: 80,  strength: 80, endurance: 40 }, color: 'var(--bw-magenta)' },
  { name: 'mage',     desc: 'Raw power, glass cannon',                base: { health: 90,  strength: 90, endurance: 25 }, color: 'var(--bw-cyan)' },
  { name: 'ranger',   desc: 'Balanced, adaptable',                    base: { health: 110, strength: 55, endurance: 55 }, color: 'var(--bw-yellow)' },
  { name: 'support',  desc: 'Survival specialist, heals and endures', base: { health: 120, strength: 30, endurance: 70 }, color: 'var(--bw-orange)' },
];

const MODELS = [
  'claude-sonnet-4-6',
  'claude-haiku-4-5-20251001',
  'gpt-4o',
  'gpt-4o-mini',
  'gemini-pro',
];

const TOKEN_LIMIT = 2048;
const PROMPT_CHAR_PER_TOKEN = 4; // rough estimate for token counter
const MAX_LEVEL = 24;
const POINTS_PER_LEVEL = 2;

export default function ChampionBuilderPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [archetypeName, setArchetypeName] = useState('tank');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState(MODELS[0]);
  const [level] = useState(MAX_LEVEL);
  const [spent, setSpent] = useState({ health: 0, strength: 0, endurance: 0 });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const archetype = useMemo(() => ARCHETYPES.find(a => a.name === archetypeName), [archetypeName]);
  const totalPoints = (level - 1) * POINTS_PER_LEVEL;
  const usedPoints = spent.health + spent.strength + spent.endurance;
  const remaining = totalPoints - usedPoints;

  const tokenCount = Math.ceil(systemPrompt.length / PROMPT_CHAR_PER_TOKEN);
  const tokenOver = tokenCount > TOKEN_LIMIT;

  function changeStat(stat, delta) {
    setSpent(prev => {
      const next = { ...prev };
      const proposed = (prev[stat] || 0) + delta;
      if (proposed < 0) return prev;
      const newUsed = (prev.health + prev.strength + prev.endurance) - prev[stat] + proposed;
      if (newUsed > totalPoints) return prev;
      next[stat] = proposed;
      return next;
    });
  }

  function selectArchetype(a) {
    setArchetypeName(a);
    setSpent({ health: 0, strength: 0, endurance: 0 });
  }

  async function handleDeploy(e) {
    e.preventDefault();
    if (!name.trim()) { setError('Champion needs a name'); return; }
    if (tokenOver) { setError('System prompt exceeds token budget'); return; }
    setError('');
    setLoading(true);
    try {
      await createChampion({
        name: name.trim(),
        archetype: archetypeName,
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
    <form onSubmit={handleDeploy} className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} FORGE / NEW CHAMPION</h1>

      {/* PREVIEW */}
      <Panel style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 16 }}>
        <div style={{
          padding: 12,
          background: `linear-gradient(180deg, ${archetype.color}33 0%, transparent 80%)`,
          boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line-2)',
        }}>
          <Sprite kind={archetypeSprite(archetypeName)} scale={6} glow={archetype.color} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value.slice(0, 20))}
            placeholder="CHAMPION NAME"
            maxLength={20}
            style={{
              width: '100%',
              fontFamily: 'var(--font-pixel)',
              fontSize: 14,
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
              color: 'var(--bw-acid)',
            }}
          />
          <div style={{ marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)' }}>
            LV.{level} · {archetypeName.toUpperCase()} · {model}
          </div>
        </div>
      </Panel>

      {/* ARCHETYPE PILLS */}
      <Panel>
        <div className="bw-h3">CLASS</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {ARCHETYPES.map(a => (
            <button
              key={a.name}
              type="button"
              onClick={() => selectArchetype(a.name)}
              style={{
                all: 'unset',
                cursor: 'pointer',
                padding: '8px 12px',
                fontFamily: 'var(--font-pixel)',
                fontSize: 9,
                letterSpacing: '0.08em',
                background: archetypeName === a.name ? a.color : 'var(--bw-panel-2)',
                color: archetypeName === a.name ? '#0a0a12' : 'var(--bw-ink-dim)',
                boxShadow: archetypeName === a.name
                  ? 'inset -2px -2px 0 0 #000, inset 2px 2px 0 0 rgba(255,255,255,0.4)'
                  : 'inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.15)',
              }}
            >
              {a.name.toUpperCase()}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 10, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)' }}>
          {archetype.desc}
        </div>
      </Panel>

      {/* SYSTEM PROMPT */}
      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div className="bw-h3">SYSTEM PROMPT · STRATEGY</div>
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: 10,
            color: tokenOver ? 'var(--bw-blood)' : 'var(--bw-ink-low)',
          }}>
            {tokenCount}/{TOKEN_LIMIT} TOK
          </div>
        </div>
        <div style={{ position: 'relative' }}>
          <textarea
            rows={5}
            value={systemPrompt}
            onChange={e => setSystemPrompt(e.target.value)}
            placeholder="> heal at 30% hp. focus weakest enemy. open with power_surge if 3+ AP."
            style={{ width: '100%', resize: 'vertical', fontFamily: 'var(--font-mono)', color: 'var(--bw-acid)' }}
          />
          <span className="blink" style={{
            position: 'absolute', right: 12, bottom: 10,
            fontFamily: 'var(--font-mono)', color: 'var(--bw-acid)',
          }}>_</span>
        </div>
      </Panel>

      {/* STAT POINTS */}
      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div className="bw-h3">STATS · LV.{level}</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: remaining > 0 ? 'var(--bw-acid)' : 'var(--bw-ink-low)' }}>
            {remaining}/{totalPoints} UNSPENT · EARN {POINTS_PER_LEVEL}/LEVEL
          </div>
        </div>
        <div className="bw-stack">
          {[
            { key: 'health',    label: 'HEALTH',    color: 'var(--bw-acid)' },
            { key: 'strength',  label: 'STRENGTH',  color: 'var(--bw-blood)' },
            { key: 'endurance', label: 'ENDURANCE', color: 'var(--bw-cyan)' },
          ].map(stat => (
            <StatRow
              key={stat.key}
              label={stat.label}
              base={archetype.base[stat.key]}
              spent={spent[stat.key]}
              color={stat.color}
              onInc={() => changeStat(stat.key, +1)}
              onDec={() => changeStat(stat.key, -1)}
              canInc={remaining > 0}
              canDec={spent[stat.key] > 0}
            />
          ))}
        </div>
      </Panel>

      {/* LOADOUT (cosmetic — backend doesn't accept yet) */}
      <Panel>
        <div className="bw-h3">LOADOUT · GEAR</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginTop: 8 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Slot key={i} label={`G${i + 1}`} />
          ))}
        </div>
        <div className="bw-h3" style={{ marginTop: 18 }}>SKILLS</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 8 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Slot key={i} label={`S${i + 1}`}>
              {i === 0 && <ItemIcon kind="staff" scale={3} />}
            </Slot>
          ))}
        </div>
      </Panel>

      {/* AI MODEL */}
      <Panel>
        <div className="bw-h3">AI MODEL</div>
        <select value={model} onChange={e => setModel(e.target.value)} style={{ width: '100%', marginBottom: 12 }}>
          {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <div className="bw-h3">API KEY (OPTIONAL · ENCRYPTED AT REST)</div>
        <input
          type="password"
          value={apiKey}
          onChange={e => setApiKey(e.target.value)}
          placeholder="sk-… or your provider key"
          autoComplete="off"
          style={{ width: '100%' }}
        />
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-low)', marginTop: 6 }}>
          NO KEY = MOCKBOT (RANDOM ACTIONS)
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
        <PixelButton variant="acid" type="submit" full disabled={loading} style={{ height: 56, fontSize: 12 }}>
          {loading ? 'DEPLOYING…' : 'DEPLOY ⚔'}
        </PixelButton>
      </div>
    </form>
  );
}

function StatRow({ label, base, spent, color, onInc, onDec, canInc, canDec }) {
  const total = base + spent;
  const baseFraction = base / Math.max(1, base + spent + 30);
  const spentFraction = spent / Math.max(1, base + spent + 30);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr 110px', gap: 12, alignItems: 'center' }}>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.08em', color: 'var(--bw-ink)' }}>
        {label}
      </div>
      <div>
        <div style={{ height: 14, background: 'var(--bw-bg)', boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)', display: 'flex' }}>
          <div style={{ width: `${Math.min(100, baseFraction * 100)}%`, background: color, opacity: 0.4 }} />
          <div style={{ width: `${Math.min(100, spentFraction * 100)}%`, background: color }} />
        </div>
        <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)' }}>
          {base} <span style={{ color: 'var(--bw-acid)' }}>+{spent}</span> = <span style={{ color, fontWeight: 800 }}>{total}</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
        <PixelButton variant="ghost" type="button" onClick={onDec} disabled={!canDec}
          style={{ padding: '6px 10px', fontSize: 10, minWidth: 36 }}>−1</PixelButton>
        <PixelButton variant="acid" type="button" onClick={onInc} disabled={!canInc}
          style={{ padding: '6px 10px', fontSize: 10, minWidth: 36 }}>+1</PixelButton>
      </div>
    </div>
  );
}
