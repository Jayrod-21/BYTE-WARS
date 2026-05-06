import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listChampions } from '../services/api';
import { PixelButton, Pill, Sprite, archetypeSprite, Panel } from '../ui/primitives';

const ROSTER_MAX = 5;

const ARCHETYPE_COLORS = {
  tank: 'var(--bw-acid)',
  assassin: 'var(--bw-magenta)',
  mage: 'var(--bw-cyan)',
  ranger: 'var(--bw-yellow)',
  support: 'var(--bw-orange)',
};

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

  const slots = [...champions];
  const empty = Math.max(0, ROSTER_MAX - slots.length);

  return (
    <div className="bw-stack-lg">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <h1 className="bw-h1" style={{ marginBottom: 0 }}>{'>'} ROSTER · {champions.length}/{ROSTER_MAX}</h1>
        <Link to="/champions/new" style={{ textDecoration: 'none' }}>
          <PixelButton variant="acid">+ FORGE NEW</PixelButton>
        </Link>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <FilterChip active={!filter} onClick={() => setFilter('')}>ALL</FilterChip>
        {['tank', 'assassin', 'mage', 'ranger', 'support'].map(a => (
          <FilterChip key={a} active={filter === a} onClick={() => setFilter(filter === a ? '' : a)}>
            {a.toUpperCase()}
          </FilterChip>
        ))}
      </div>

      {error && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>}
      {loading && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING ROSTER…</div>}

      {!loading && (
        <div style={{ display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
          {slots.map(c => <ChampionCard key={c.id} champion={c} />)}
          {filter === '' && Array.from({ length: empty }).map((_, i) => (
            <Link key={`empty-${i}`} to="/champions/new" style={{ textDecoration: 'none' }}>
              <EmptySlot />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function ChampionCard({ champion }) {
  const sprite = archetypeSprite(champion.archetype);
  const archColor = ARCHETYPE_COLORS[champion.archetype] || 'var(--bw-line)';
  const wins = champion.wins ?? 0;
  const losses = champion.losses ?? 0;
  const total = wins + losses;
  const winrate = total > 0 ? Math.round((wins / total) * 100) : null;

  return (
    <Panel style={{ padding: 0, position: 'relative', overflow: 'hidden' }}>
      <div style={{
        height: 110,
        background: `linear-gradient(180deg, ${archColor}22 0%, transparent 80%)`,
        position: 'relative',
        borderBottom: '2px solid var(--bw-line)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <Sprite kind={sprite} scale={4} glow={archColor} />
      </div>
      <div style={{ padding: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6, gap: 8 }}>
          <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 10, letterSpacing: '0.05em', color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {(champion.name || 'UNNAMED').toUpperCase()}
          </div>
          <Pill color={archColor}>{champion.archetype}</Pill>
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)', marginBottom: 10 }}>
          LV.{champion.level ?? 1} · {champion.model || 'mock-bot'}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 10 }}>
          <StatBlock label="HP" value={champion.stats?.health ?? 0} color="var(--bw-acid)" />
          <StatBlock label="STR" value={champion.stats?.strength ?? 0} color="var(--bw-blood)" />
          <StatBlock label="END" value={champion.stats?.endurance ?? 0} color="var(--bw-cyan)" />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-dim)', paddingTop: 8, borderTop: '2px dashed var(--bw-line)' }}>
          <span>{wins}W / {losses}L</span>
          {winrate !== null && (
            <span style={{ color: winrate >= 60 ? 'var(--bw-acid)' : winrate >= 45 ? 'var(--bw-yellow)' : 'var(--bw-blood)' }}>
              {winrate}%
            </span>
          )}
        </div>
      </div>
    </Panel>
  );
}

function EmptySlot() {
  return (
    <div style={{
      minHeight: 250,
      backgroundImage: 'repeating-linear-gradient(45deg, #11111c 0 6px, #1a1a2a 6px 12px)',
      boxShadow: 'inset 0 0 0 2px var(--bw-line)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      cursor: 'pointer',
      transition: 'filter 80ms',
    }}
    onMouseEnter={e => e.currentTarget.style.filter = 'brightness(1.3)'}
    onMouseLeave={e => e.currentTarget.style.filter = 'brightness(1)'}
    >
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 28, color: 'var(--bw-line-2)' }}>+</div>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.1em', color: 'var(--bw-ink-low)' }}>NEW CHAMPION</div>
    </div>
  );
}

function StatBlock({ label, value, color }) {
  return (
    <div style={{
      padding: '6px 4px',
      background: 'var(--bw-bg)',
      boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
      textAlign: 'center',
    }}>
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 6, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 2 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}

function FilterChip({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        all: 'unset',
        cursor: 'pointer',
        padding: '6px 10px',
        fontFamily: 'var(--font-pixel)',
        fontSize: 8,
        letterSpacing: '0.08em',
        background: active ? 'var(--bw-acid)' : 'var(--bw-panel-2)',
        color: active ? '#0a1a00' : 'var(--bw-ink-dim)',
        boxShadow: 'inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.2)',
      }}
    >
      {children}
    </button>
  );
}
