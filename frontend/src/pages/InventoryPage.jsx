import { useState, useEffect } from 'react';
import { getUser } from '../services/api';

const RARITY_COLORS = {
  common: '#aaaaaa',
  uncommon: '#44ff44',
  rare: '#4488ff',
  legendary: '#ffaa00',
};

export default function InventoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState(''); // gear, skill, or ''

  const user = getUser();
  const ownerId = user?.id || 'demo-user';

  useEffect(() => { loadInventory(); }, []);

  async function loadInventory() {
    setLoading(true);
    try {
      let resp = await fetch(`/api/nft/inventory/${ownerId}`);
      let data = await resp.json();
      if (data.length === 0) {
        // Generate starter inventory
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

  const filtered = filter ? items.filter(i => i.nft_type === filter) : items;

  return (
    <div>
      <h1 className="page-title">NFT Inventory</h1>

      <div className="flex gap-8 mb-12">
        <button className={`btn btn-sm ${!filter ? 'active' : ''}`} onClick={() => setFilter('')}>All ({items.length})</button>
        <button className={`btn btn-sm ${filter === 'gear' ? 'active' : ''}`} onClick={() => setFilter('gear')}>
          Gear ({items.filter(i => i.nft_type === 'gear').length})
        </button>
        <button className={`btn btn-sm ${filter === 'skill' ? 'active' : ''}`} onClick={() => setFilter('skill')}>
          Skills ({items.filter(i => i.nft_type === 'skill').length})
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading inventory...</div>}

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
          </div>
        ))}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          No items found.
        </div>
      )}
    </div>
  );
}
