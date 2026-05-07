import { useState, useEffect, useMemo } from 'react';
import {
  getUser, createListing, getUserChests,
  getInventory, generateInventory,
} from '../services/api';
import {
  PixelButton, Pill, ItemIcon, rarityColor, Panel, SolDiamond,
} from '../ui/primitives';

function iconForItem(item) {
  const t = item?.nft_type || '';
  const archetype = item?.archetype_affinity || '';
  if (t === 'skill') {
    if (archetype === 'mage') return 'staff';
    if (archetype === 'ranger') return 'bow';
    return 'scroll';
  }
  // gear default → sword/shield by name
  const n = (item?.name || '').toLowerCase();
  if (n.includes('shield')) return 'shield';
  if (n.includes('bow')) return 'bow';
  if (n.includes('staff')) return 'staff';
  if (n.includes('potion')) return 'potion';
  if (n.includes('crown') || n.includes('helm')) return 'crown';
  return 'sword';
}

export default function InventoryPage() {
  const user = getUser();
  const ownerId = user?.id || 'demo-user';

  const [items, setItems] = useState([]);
  const [chests, setChests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('');
  const [tab, setTab] = useState('inventory');
  const [selected, setSelected] = useState(null);
  const [listingPrice, setListingPrice] = useState('');
  const [listingFor, setListingFor] = useState(null);

  useEffect(() => { loadInventory(); loadChests(); }, []);

  async function loadInventory() {
    setLoading(true);
    setError('');
    try {
      let data = await getInventory(ownerId);
      if (!Array.isArray(data) || data.length === 0) {
        data = await generateInventory(ownerId);
      }
      setItems(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data[0]) setSelected(data[0]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadChests() {
    try {
      const data = await getUserChests(ownerId);
      setChests(data || []);
    } catch { /* ignore */ }
  }

  async function handleList() {
    if (!listingFor) return;
    const price = parseFloat(listingPrice);
    if (!(price > 0)) { setError('Enter a valid price'); return; }
    setError('');
    try {
      await createListing(listingFor.id, ownerId, price);
      setListingFor(null);
      setListingPrice('');
      // Reload — listed items might disappear from inventory
      loadInventory();
    } catch (err) {
      setError(err.message);
    }
  }

  const filtered = useMemo(
    () => filter ? items.filter(i => i.nft_type === filter) : items,
    [items, filter],
  );

  const counts = useMemo(() => ({
    gear: items.filter(i => i.nft_type === 'gear').length,
    skill: items.filter(i => i.nft_type === 'skill').length,
  }), [items]);

  return (
    <div className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} BAG · {items.length} ITEMS</h1>

      <div style={{ display: 'flex', gap: 8 }}>
        <TabButton active={tab === 'inventory'} onClick={() => setTab('inventory')}>INVENTORY · {items.length}</TabButton>
        <TabButton active={tab === 'chests'} onClick={() => setTab('chests')}>CHESTS · {chests.length}</TabButton>
      </div>

      {error && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)' }}>! {error}</div>}
      {loading && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>LOADING…</div>}

      {tab === 'inventory' && (
        <div className="bw-split">
          <div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
              <Chip active={!filter} onClick={() => setFilter('')}>ALL · {items.length}</Chip>
              <Chip active={filter === 'gear'} onClick={() => setFilter(filter === 'gear' ? '' : 'gear')}>GEAR · {counts.gear}</Chip>
              <Chip active={filter === 'skill'} onClick={() => setFilter(filter === 'skill' ? '' : 'skill')}>SKILLS · {counts.skill}</Chip>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: 10 }}>
              {filtered.map(item => (
                <ItemCard key={item.id} item={item} active={selected?.id === item.id} onClick={() => setSelected(item)} />
              ))}
              {!loading && filtered.length === 0 && (
                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 30, fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>
                  NO ITEMS MATCH FILTER
                </div>
              )}
            </div>
          </div>

          {/* Detail panel */}
          {selected ? (
            <Panel style={{ position: 'sticky', top: 80 }}>
              <div style={{ display: 'flex', justifyContent: 'center', padding: 18, background: 'var(--bw-bg)', boxShadow: `inset 0 0 0 2px ${rarityColor(selected.rarity)}` }}>
                <ItemIcon kind={iconForItem(selected)} scale={6} />
              </div>
              <div style={{ marginTop: 14 }}>
                <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 11, letterSpacing: '0.05em', color: 'var(--bw-ink)', marginBottom: 4 }}>
                  {(selected.name || '').replace(/_/g, ' ').toUpperCase()}
                </div>
                <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                  <Pill color={rarityColor(selected.rarity)}>{selected.rarity}</Pill>
                  <Pill color="var(--bw-line-2)" textColor="var(--bw-ink)">{selected.nft_type}</Pill>
                  {selected.archetype_affinity && (
                    <Pill color="var(--bw-cyan)">{selected.archetype_affinity}</Pill>
                  )}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', marginBottom: 12 }}>
                  {selected.description || '—'}
                </div>

                {/* Stats */}
                {selected.nft_type === 'gear' && selected.stat_bonuses && (
                  <div className="panel-sunken" style={{ padding: 10, marginBottom: 12 }}>
                    {Object.entries(selected.stat_bonuses).map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                        <span style={{ color: 'var(--bw-ink-dim)' }}>{k.toUpperCase()}</span>
                        <span style={{ color: 'var(--bw-acid)', fontWeight: 800 }}>+{v}</span>
                      </div>
                    ))}
                  </div>
                )}

                {selected.nft_type === 'skill' && selected.skill_action && (
                  <div className="panel-sunken" style={{ padding: 10, marginBottom: 12 }}>
                    <Row label="AP COST" value={selected.skill_action.action_point_cost} color="var(--bw-cyan)" />
                    {selected.skill_action.damage_range && (
                      <Row label="DAMAGE" value={`${selected.skill_action.damage_range[0]}-${selected.skill_action.damage_range[1]}`} color="var(--bw-blood)" />
                    )}
                    {selected.skill_action.heal_range && (
                      <Row label="HEAL" value={`${selected.skill_action.heal_range[0]}-${selected.skill_action.heal_range[1]}`} color="var(--bw-acid)" />
                    )}
                  </div>
                )}

                {/* Actions */}
                {listingFor?.id === selected.id ? (
                  <div className="bw-stack">
                    <input
                      type="number"
                      value={listingPrice}
                      onChange={e => setListingPrice(e.target.value)}
                      min="0.01"
                      step="0.01"
                      placeholder="price (SOL)"
                      style={{ width: '100%' }}
                    />
                    <div style={{ display: 'flex', gap: 6 }}>
                      <PixelButton variant="acid" onClick={handleList} full>LIST IT</PixelButton>
                      <PixelButton variant="ghost" onClick={() => setListingFor(null)} aria-label="Cancel listing">X</PixelButton>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 6 }}>
                    <PixelButton variant="cyan" full disabled title="Equip flow not wired">EQUIP</PixelButton>
                    <PixelButton variant="magenta" onClick={() => { setListingFor(selected); setListingPrice(''); }}>LIST</PixelButton>
                  </div>
                )}
              </div>
            </Panel>
          ) : (
            <Panel><div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>SELECT AN ITEM</div></Panel>
          )}
        </div>
      )}

      {tab === 'chests' && (
        <div className="bw-stack">
          {chests.length === 0 && (
            <Panel><div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>NO LOOT CHESTS YET. WIN A MATCH.</div></Panel>
          )}
          {chests.map(chest => (
            <Panel key={chest.id}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 10, color: 'var(--bw-yellow)' }}>
                  ◇ LOOT CHEST · {chest.items?.length || 0} ITEMS
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--bw-ink-low)' }}>
                  {chest.created_at ? new Date(chest.created_at).toLocaleDateString() : ''}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
                {chest.items?.map((item, i) => (
                  <div key={i} style={{
                    padding: 8, display: 'flex', gap: 8, alignItems: 'center',
                    background: 'var(--bw-bg)',
                    boxShadow: `inset 0 0 0 2px ${rarityColor(item.rarity)}`,
                  }}>
                    <ItemIcon kind={iconForItem(item)} scale={2} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {(item.name || '').replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: rarityColor(item.rarity) }}>
                        {(item.rarity || '').toUpperCase()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}

function ItemCard({ item, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        all: 'unset',
        cursor: 'pointer',
        padding: 8,
        background: 'var(--bw-bg)',
        boxShadow: active
          ? `inset 0 0 0 3px ${rarityColor(item.rarity)}, 0 0 12px ${rarityColor(item.rarity)}55`
          : `inset 0 0 0 2px ${rarityColor(item.rarity)}`,
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
        transition: 'transform 80ms steps(2)',
      }}
    >
      <ItemIcon kind={iconForItem(item)} scale={3} />
      <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 6, letterSpacing: '0.05em', textAlign: 'center', color: 'var(--bw-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 100 }}>
        {(item.name || '').replace(/_/g, ' ').toUpperCase()}
      </div>
    </button>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, padding: '2px 0' }}>
      <span style={{ color: 'var(--bw-ink-dim)', letterSpacing: '0.06em' }}>{label}</span>
      <span style={{ color, fontWeight: 800 }}>{value}</span>
    </div>
  );
}

function Chip({ active, children, onClick }) {
  return (
    <button type="button" onClick={onClick} style={{
      all: 'unset', cursor: 'pointer',
      padding: '6px 10px',
      fontFamily: 'var(--font-pixel)', fontSize: 8, letterSpacing: '0.08em',
      background: active ? 'var(--bw-acid)' : 'var(--bw-panel-2)',
      color: active ? '#0a1a00' : 'var(--bw-ink-dim)',
      boxShadow: 'inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.2)',
    }}>{children}</button>
  );
}

function TabButton({ active, children, onClick }) {
  return (
    <button type="button" onClick={onClick} style={{
      all: 'unset', cursor: 'pointer',
      padding: '8px 14px',
      fontFamily: 'var(--font-pixel)', fontSize: 9, letterSpacing: '0.08em',
      color: active ? 'var(--bw-acid)' : 'var(--bw-ink-low)',
      borderBottom: active ? '3px solid var(--bw-acid)' : '3px solid transparent',
    }}>{children}</button>
  );
}
