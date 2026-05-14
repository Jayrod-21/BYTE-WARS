import { useState, useEffect, useMemo } from 'react';
import { browseMarketplace, buyListing, getUser, walletForUser, airdropSol } from '../services/api';
import {
  PixelButton, Pill, ItemIcon, rarityColor, Panel, SolDiamond,
} from '../ui/primitives';

const RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary'];

function iconForItem(nft) {
  const t = nft?.nft_type || '';
  if (t === 'skill') {
    if (nft?.archetype_affinity === 'mage') return 'staff';
    if (nft?.archetype_affinity === 'ranger') return 'bow';
    return 'scroll';
  }
  const n = (nft?.name || '').toLowerCase();
  if (n.includes('shield')) return 'shield';
  if (n.includes('bow')) return 'bow';
  if (n.includes('staff')) return 'staff';
  if (n.includes('potion')) return 'potion';
  if (n.includes('crown') || n.includes('helm')) return 'crown';
  return 'sword';
}

export default function MarketplacePage() {
  const user = getUser();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [buying, setBuying] = useState('');

  const [typeFilter, setTypeFilter] = useState('');
  const [rarityFilter, setRarityFilter] = useState('');
  const [archetypeFilter, setArchetypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [maxPrice, setMaxPrice] = useState(100);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => { loadListings(); }, [typeFilter, rarityFilter, archetypeFilter]);

  async function loadListings() {
    setLoading(true);
    setError('');
    try {
      const data = await browseMarketplace({
        nft_type: typeFilter || undefined,
        rarity: rarityFilter || undefined,
        archetype: archetypeFilter || undefined,
      });
      setListings(data || []);
      if (data?.[0]) setSelectedId(data[0].id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBuy(listingId) {
    if (!user) { setError('Login to buy'); return; }
    setBuying(listingId);
    setError('');
    try {
      const wallet = walletForUser(user);
      await buyListing(listingId, user.id, wallet);
      loadListings();
    } catch (err) {
      setError(err.message);
    } finally {
      setBuying('');
    }
  }

  async function handleAirdrop() {
    if (!user) return;
    try {
      await airdropSol(walletForUser(user), 10);
      setError('Airdropped 10 SOL — try the purchase again.');
    } catch (err) {
      setError(`Airdrop failed: ${err.message}`);
    }
  }

  const filtered = useMemo(() => {
    return listings.filter(l => {
      if (search && !(l.nft_snapshot?.name || '').toLowerCase().includes(search.toLowerCase())) return false;
      if (l.price_sol > maxPrice) return false;
      return true;
    });
  }, [listings, search, maxPrice]);

  const selected = filtered.find(l => l.id === selectedId) || filtered[0];

  return (
    <div className="bw-stack-lg">
      <h1 className="bw-h1">{'>'} MARKETPLACE · {filtered.length} LISTINGS</h1>

      {/* Filter bar */}
      <Panel>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">ALL TYPES</option>
            <option value="gear">GEAR</option>
            <option value="skill">SKILLS</option>
          </select>
          <select value={rarityFilter} onChange={e => setRarityFilter(e.target.value)}>
            <option value="">ALL RARITIES</option>
            {RARITIES.map(r => <option key={r} value={r}>{r.toUpperCase()}</option>)}
          </select>
          <select value={archetypeFilter} onChange={e => setArchetypeFilter(e.target.value)}>
            <option value="">ALL ARCHETYPES</option>
            <option value="tank">TANK</option>
            <option value="assassin">ASSASSIN</option>
            <option value="mage">MAGE</option>
            <option value="ranger">RANGER</option>
            <option value="support">SUPPORT</option>
          </select>
          <input
            type="search"
            placeholder="SEARCH NAME…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div style={{ marginTop: 12 }}>
          <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: 'var(--bw-ink-low)', letterSpacing: '0.1em', marginBottom: 4 }}>
            MAX PRICE · {maxPrice} SOL
          </div>
          <input type="range" min="0.1" max="100" step="0.1" value={maxPrice}
            onChange={e => setMaxPrice(parseFloat(e.target.value))}
            style={{ width: '100%' }} />
        </div>
      </Panel>

      {error && (
        <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-blood)', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span>! {error}</span>
          {/Insufficient balance/i.test(error) && (
            <PixelButton variant="cyan" type="button" onClick={handleAirdrop}>+10 SOL AIRDROP</PixelButton>
          )}
        </div>
      )}
      {loading && <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>SCANNING MARKETPLACE…</div>}

      {!loading && (
        <div className="bw-split">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
            {filtered.map(listing => {
              const nft = listing.nft_snapshot || {};
              const isMine = listing.seller_id === user?.id;
              return (
                <button
                  type="button"
                  key={listing.id}
                  onClick={() => setSelectedId(listing.id)}
                  style={{
                    all: 'unset',
                    cursor: 'pointer',
                    padding: 10,
                    background: 'var(--bw-bg)',
                    boxShadow: selectedId === listing.id
                      ? `inset 0 0 0 3px ${rarityColor(nft.rarity)}, 0 0 12px ${rarityColor(nft.rarity)}55`
                      : `inset 0 0 0 2px ${rarityColor(nft.rarity)}`,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                  }}
                >
                  <ItemIcon kind={iconForItem(nft)} scale={3} />
                  <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 7, color: 'var(--bw-ink)', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 110 }}>
                    {(nft.name || '').replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-yellow)', fontWeight: 800 }}>
                    <SolDiamond /> {listing.price_sol}
                  </div>
                  {isMine && <Pill color="var(--bw-magenta)" style={{ fontSize: 6 }}>YOURS</Pill>}
                </button>
              );
            })}
            {filtered.length === 0 && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 30, fontFamily: 'var(--font-mono)', color: 'var(--bw-ink-dim)' }}>
                NO LISTINGS MATCH FILTERS.
              </div>
            )}
          </div>

          {selected && (
            <FeaturedItem
              listing={selected}
              isMine={selected.seller_id === user?.id}
              buying={buying === selected.id}
              onBuy={() => handleBuy(selected.id)}
            />
          )}
        </div>
      )}
    </div>
  );
}

function FeaturedItem({ listing, isMine, buying, onBuy }) {
  const nft = listing.nft_snapshot || {};
  return (
    <Panel style={{ position: 'sticky', top: 80 }}>
      <div style={{
        display: 'flex', justifyContent: 'center',
        padding: 24, background: 'var(--bw-bg)',
        boxShadow: `inset 0 0 0 2px ${rarityColor(nft.rarity)}`,
      }}>
        <ItemIcon kind={iconForItem(nft)} scale={6} />
      </div>
      <div style={{ marginTop: 14 }}>
        <div style={{ fontFamily: 'var(--font-pixel)', fontSize: 12, color: 'var(--bw-ink)', letterSpacing: '0.05em', marginBottom: 6 }}>
          {(nft.name || '').replace(/_/g, ' ').toUpperCase()}
        </div>
        <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
          <Pill color={rarityColor(nft.rarity)}>{nft.rarity}</Pill>
          <Pill color="var(--bw-line-2)" textColor="var(--bw-ink)">{nft.nft_type}</Pill>
          {nft.archetype_affinity && <Pill color="var(--bw-cyan)">{nft.archetype_affinity}</Pill>}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--bw-ink-dim)', marginBottom: 12 }}>
          {nft.description || '—'}
        </div>

        {nft.nft_type === 'gear' && nft.stat_bonuses && (
          <div className="panel-sunken" style={{ padding: 10, marginBottom: 12 }}>
            {Object.entries(nft.stat_bonuses).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                <span style={{ color: 'var(--bw-ink-dim)' }}>{k.toUpperCase()}</span>
                <span style={{ color: 'var(--bw-acid)', fontWeight: 800 }}>+{v}</span>
              </div>
            ))}
          </div>
        )}

        {nft.nft_type === 'skill' && nft.skill_action && (
          <div className="panel-sunken" style={{ padding: 10, marginBottom: 12 }}>
            <Row label="AP COST" value={nft.skill_action.action_point_cost} color="var(--bw-cyan)" />
            {nft.skill_action.damage_range && (
              <Row label="DAMAGE" value={`${nft.skill_action.damage_range[0]}-${nft.skill_action.damage_range[1]}`} color="var(--bw-blood)" />
            )}
            {nft.skill_action.heal_range && (
              <Row label="HEAL" value={`${nft.skill_action.heal_range[0]}-${nft.skill_action.heal_range[1]}`} color="var(--bw-acid)" />
            )}
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontFamily: 'var(--font-pixel)', fontSize: 8, color: 'var(--bw-ink-low)' }}>PRICE</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 800, color: 'var(--bw-yellow)' }}>
            <SolDiamond size={10} /> {listing.price_sol} SOL
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <PixelButton variant="acid" full onClick={onBuy} disabled={isMine || buying}>
            {buying ? 'PURCHASING…' : isMine ? 'YOUR LISTING' : `BUY NOW ◇ ${listing.price_sol}`}
          </PixelButton>
          <div style={{ display: 'flex', gap: 6 }}>
            <PixelButton variant="ghost" full disabled title="Offers not implemented">MAKE OFFER</PixelButton>
            <PixelButton variant="ghost" full disabled title="Watchlist not implemented">WATCH</PixelButton>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function Row({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, padding: '2px 0' }}>
      <span style={{ color: 'var(--bw-ink-dim)' }}>{label}</span>
      <span style={{ color, fontWeight: 800 }}>{value}</span>
    </div>
  );
}
