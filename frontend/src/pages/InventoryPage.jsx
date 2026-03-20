import { useState, useEffect } from 'react';
import { getUser, createListing, getUserChests } from '../services/api';

const RARITY_COLORS = {
  common: '#aaaaaa',
  uncommon: '#44ff44',
  rare: '#4488ff',
  legendary: '#ffaa00',
};

export default function InventoryPage() {
  const [items, setItems] = useState([]);
  const [chests, setChests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState(''); // gear, skill, or ''
  const [listingPrice, setListingPrice] = useState({});
  const [listingItem, setListingItem] = useState(null);
  const [tab, setTab] = useState('inventory'); // inventory or chests

  const user = getUser();
  const ownerId = user?.id || 'demo-user';

  useEffect(() => { loadInventory(); loadChests(); }, []);

  async function loadInventory() {
    setLoading(true);
    try {
      let resp = await fetch(`/api/nft/inventory/${ownerId}`);
      let data = await resp.json();
      if (data.length === 0) {
        resp = await fetch(`/api/nft/inventory/${ownerId}/generate`, { method: 'POST' });
        data = await resp.json();
      }
      setItems(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadChests() {
    try {
      const data = await getUserChests(ownerId);
      setChests(data);
    } catch {}
  }

  async function handleList(itemId) {
    const price = parseFloat(listingPrice[itemId] || '0');
    if (price <= 0) { setError('Enter a valid price'); return; }
    setError('');
    try {
      await createListing(itemId, ownerId, price);
      setListingItem(null);
      setListingPrice({});
      alert('Listed on marketplace!');
    } catch (err) {
      setError(err.message);
    }
  }

  const filtered = filter ? items.filter(i => i.nft_type === filter) : items;

  return (
    <div>
      <h1 className="page-title">NFT Inventory</h1>

      {/* Tabs */}
      <div className="flex gap-8 mb-12">
        <button className={`btn btn-sm ${tab === 'inventory' ? 'active' : ''}`}
          onClick={() => setTab('inventory')}>
          Inventory ({items.length})
        </button>
        <button className={`btn btn-sm ${tab === 'chests' ? 'active' : ''}`}
          onClick={() => setTab('chests')}>
          Loot Chests ({chests.length})
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading inventory...</div>}

      {tab === 'inventory' && (
        <>
          <div className="flex gap-8 mb-12">
            <button className={`btn btn-sm ${!filter ? 'active' : ''}`} onClick={() => setFilter('')}>All</button>
            <button className={`btn btn-sm ${filter === 'gear' ? 'active' : ''}`} onClick={() => setFilter('gear')}>
              Gear ({items.filter(i => i.nft_type === 'gear').length})
            </button>
            <button className={`btn btn-sm ${filter === 'skill' ? 'active' : ''}`} onClick={() => setFilter('skill')}>
              Skills ({items.filter(i => i.nft_type === 'skill').length})
            </button>
          </div>

          <div className="grid grid-2">
            {filtered.map(item => (
              <div key={item.id} className="card" style={{
                borderColor: RARITY_COLORS[item.rarity] || '#333',
              }}>
                <div className="flex flex-between flex-center">
                  <strong style={{ textTransform: 'capitalize' }}>
                    {item.name.replace(/_/g, ' ')}
                  </strong>
                  <span style={{
                    color: RARITY_COLORS[item.rarity],
                    fontSize: '0.75em',
                    textTransform: 'uppercase',
                  }}>
                    {item.rarity}
                  </span>
                </div>
                <div style={{ fontSize: '0.8em', color: 'var(--text-dim)', marginTop: 4 }}>
                  {item.description}
                </div>
                <div className="flex flex-between mt-12" style={{ fontSize: '0.8em' }}>
                  <span style={{ color: 'var(--text-dim)' }}>
                    {item.nft_type === 'gear' ? 'Gear' : 'Skill'} | {item.archetype_affinity}
                  </span>
                  {item.nft_type === 'gear' && item.stat_bonuses && (
                    <span className="stat-value">
                      {Object.entries(item.stat_bonuses).map(([k, v]) =>
                        `${k.substring(0, 3).toUpperCase()}+${v}`
                      ).join(' ')}
                    </span>
                  )}
                  {item.nft_type === 'skill' && item.skill_action && (
                    <span className="stat-value">
                      {item.skill_action.action_point_cost}AP
                      {item.skill_action.damage_range && ` DMG:${item.skill_action.damage_range[0]}-${item.skill_action.damage_range[1]}`}
                      {item.skill_action.heal_range && ` HEAL:${item.skill_action.heal_range[0]}-${item.skill_action.heal_range[1]}`}
                    </span>
                  )}
                </div>

                {/* Sell button */}
                <div style={{ marginTop: 8, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  {listingItem === item.id ? (
                    <div className="flex gap-8">
                      <input
                        type="number"
                        className="input"
                        placeholder="Price (SOL)"
                        min="0.01"
                        step="0.01"
                        value={listingPrice[item.id] || ''}
                        onChange={e => setListingPrice({ ...listingPrice, [item.id]: e.target.value })}
                        style={{ width: '100px', fontSize: '0.85em' }}
                      />
                      <button className="btn btn-sm" onClick={() => handleList(item.id)}>Confirm</button>
                      <button className="btn btn-sm" onClick={() => setListingItem(null)}>Cancel</button>
                    </div>
                  ) : (
                    <button className="btn btn-sm" onClick={() => setListingItem(item.id)}
                      style={{ fontSize: '0.8em' }}>
                      Sell on Marketplace
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {!loading && filtered.length === 0 && (
            <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
              No items found.
            </div>
          )}
        </>
      )}

      {tab === 'chests' && (
        <div>
          {chests.length === 0 && (
            <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
              No loot chests yet. Win a match to earn your first chest!
            </div>
          )}
          {chests.map(chest => (
            <div key={chest.id} className="card mb-12" style={{ borderColor: 'var(--warning)' }}>
              <div className="flex flex-between flex-center">
                <strong style={{ color: 'var(--warning)' }}>Loot Chest</strong>
                <span style={{ fontSize: '0.75em', color: 'var(--text-dim)' }}>
                  {new Date(chest.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="grid grid-2 mt-12" style={{ gap: 8 }}>
                {chest.items.map((item, idx) => (
                  <div key={idx} style={{
                    padding: '8px',
                    border: `1px solid ${RARITY_COLORS[item.rarity] || '#333'}`,
                    borderRadius: 4,
                    fontSize: '0.85em',
                  }}>
                    <div className="flex flex-between">
                      <span style={{ textTransform: 'capitalize' }}>
                        {item.name.replace(/_/g, ' ')}
                      </span>
                      <span style={{ color: RARITY_COLORS[item.rarity], fontSize: '0.8em' }}>
                        {item.rarity}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.8em' }}>
                      {item.nft_type}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
