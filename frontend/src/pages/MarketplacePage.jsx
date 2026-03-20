import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { browseMarketplace, buyListing, getUser, getWalletBalance } from '../services/api';

const RARITY_COLORS = {
  common: '#aaaaaa',
  uncommon: '#44ff44',
  rare: '#4488ff',
  legendary: '#ffaa00',
};

export default function MarketplacePage() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [buying, setBuying] = useState('');

  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [rarityFilter, setRarityFilter] = useState('');
  const [archetypeFilter, setArchetypeFilter] = useState('');

  const user = getUser();

  useEffect(() => { loadListings(); }, [typeFilter, rarityFilter, archetypeFilter]);

  async function loadListings() {
    setLoading(true);
    try {
      const data = await browseMarketplace({
        nft_type: typeFilter || undefined,
        rarity: rarityFilter || undefined,
        archetype: archetypeFilter || undefined,
      });
      setListings(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBuy(listingId) {
    if (!user) { setError('Login to purchase'); return; }
    setBuying(listingId);
    setError('');
    try {
      const wallet = `devnet_${user.id.slice(0, 8)}`;
      await buyListing(listingId, user.id, wallet);
      loadListings();
    } catch (err) {
      setError(err.message);
    } finally {
      setBuying('');
    }
  }

  return (
    <div>
      <h1 className="page-title">NFT Marketplace</h1>

      {/* Filters */}
      <div className="flex gap-8 mb-12" style={{ flexWrap: 'wrap' }}>
        <select className="input" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
          style={{ width: 'auto', minWidth: 100 }}>
          <option value="">All Types</option>
          <option value="gear">Gear</option>
          <option value="skill">Skills</option>
        </select>
        <select className="input" value={rarityFilter} onChange={e => setRarityFilter(e.target.value)}
          style={{ width: 'auto', minWidth: 100 }}>
          <option value="">All Rarities</option>
          <option value="common">Common</option>
          <option value="uncommon">Uncommon</option>
          <option value="rare">Rare</option>
          <option value="legendary">Legendary</option>
        </select>
        <select className="input" value={archetypeFilter} onChange={e => setArchetypeFilter(e.target.value)}
          style={{ width: 'auto', minWidth: 100 }}>
          <option value="">All Archetypes</option>
          <option value="tank">Tank</option>
          <option value="assassin">Assassin</option>
          <option value="mage">Mage</option>
          <option value="ranger">Ranger</option>
          <option value="support">Support</option>
        </select>
      </div>

      {error && <div className="error mb-12">{error}</div>}
      {loading && <div className="loading">Loading marketplace...</div>}

      <div className="grid grid-2">
        {listings.map(listing => {
          const nft = listing.nft_snapshot;
          return (
            <div key={listing.id} className="card" style={{
              borderColor: RARITY_COLORS[nft.rarity] || '#333',
            }}>
              <div className="flex flex-between flex-center">
                <strong style={{ textTransform: 'capitalize' }}>
                  {nft.name.replace(/_/g, ' ')}
                </strong>
                <span style={{
                  color: RARITY_COLORS[nft.rarity],
                  fontSize: '0.75em',
                  textTransform: 'uppercase',
                }}>
                  {nft.rarity}
                </span>
              </div>
              <div style={{ fontSize: '0.8em', color: 'var(--text-dim)', marginTop: 4 }}>
                {nft.description}
              </div>
              <div className="flex flex-between mt-12" style={{ fontSize: '0.8em' }}>
                <span style={{ color: 'var(--text-dim)' }}>
                  {nft.nft_type === 'gear' ? 'Gear' : 'Skill'} | {nft.archetype_affinity}
                </span>
                {nft.nft_type === 'gear' && nft.stat_bonuses && (
                  <span className="stat-value">
                    {Object.entries(nft.stat_bonuses).map(([k, v]) =>
                      `${k.substring(0, 3).toUpperCase()}+${v}`
                    ).join(' ')}
                  </span>
                )}
                {nft.nft_type === 'skill' && nft.skill_action && (
                  <span className="stat-value">
                    {nft.skill_action.action_point_cost}AP
                    {nft.skill_action.damage_range && ` DMG:${nft.skill_action.damage_range[0]}-${nft.skill_action.damage_range[1]}`}
                    {nft.skill_action.heal_range && ` HEAL:${nft.skill_action.heal_range[0]}-${nft.skill_action.heal_range[1]}`}
                  </span>
                )}
              </div>
              <div className="flex flex-between flex-center mt-12"
                style={{ borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                <span style={{ color: 'var(--warning)', fontWeight: 'bold', fontSize: '1.1em' }}>
                  {listing.price_sol} SOL
                </span>
                <button
                  className="btn btn-sm"
                  onClick={() => handleBuy(listing.id)}
                  disabled={buying === listing.id || listing.seller_id === user?.id}
                >
                  {buying === listing.id ? 'Buying...' : 'Buy'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {!loading && listings.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          No listings found. Check back later or adjust your filters.
        </div>
      )}
    </div>
  );
}
