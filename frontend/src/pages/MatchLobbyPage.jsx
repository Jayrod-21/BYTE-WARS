import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listChampions, createMatch, startMatch, placeWager, getMatchOdds, getUser } from '../services/api';
import { requestNotificationPermission, notifyMatchComplete } from '../services/notifications';

export default function MatchLobbyPage() {
  const navigate = useNavigate();
  const [champions, setChampions] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fighting, setFighting] = useState(false);
  const [error, setError] = useState('');

  // Wager state
  const [wagerEnabled, setWagerEnabled] = useState(false);
  const [wagerChampion, setWagerChampion] = useState('');
  const [wagerAmount, setWagerAmount] = useState('0.1');
  const [matchId, setMatchId] = useState(null);
  const [odds, setOdds] = useState(null);
  const [wagerPlaced, setWagerPlaced] = useState(false);

  const user = getUser();

  useEffect(() => {
    listChampions().then(setChampions).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);

  function toggleSelect(id) {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev
    );
    // Reset wager state when selection changes
    setMatchId(null);
    setOdds(null);
    setWagerPlaced(false);
  }

  async function handleCreateMatch() {
    if (selected.length < 2) { setError('Select at least 2 champions'); return; }
    setError('');
    try {
      const match = await createMatch(selected);
      setMatchId(match.id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handlePlaceWager() {
    if (!matchId || !wagerChampion || !wagerAmount) return;
    setError('');
    try {
      const walletAddr = user?.wallet_address || `devnet_${user?.id || 'anon'}`;
      await placeWager(matchId, user?.id || 'anon', walletAddr, wagerChampion, parseFloat(wagerAmount));
      setWagerPlaced(true);
      // Refresh odds
      const newOdds = await getMatchOdds(matchId);
      setOdds(newOdds);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleFight() {
    if (!matchId) {
      // Create match first if not yet created
      if (selected.length < 2) { setError('Select at least 2 champions'); return; }
      setError('');
      try {
        const match = await createMatch(selected);
        setMatchId(match.id);
        setFighting(true);
        await requestNotificationPermission();
        const result = await startMatch(match.id);
        notifyMatchComplete(match.id, result.winner_name);
        navigate(`/playback/${match.id}`);
      } catch (err) {
        setError(err.message);
        setFighting(false);
      }
    } else {
      setFighting(true);
      try {
        await requestNotificationPermission();
        const result = await startMatch(matchId);
        notifyMatchComplete(matchId, result.winner_name);
        navigate(`/playback/${matchId}`);
      } catch (err) {
        setError(err.message);
        setFighting(false);
      }
    }
  }

  const selectedChampions = champions.filter(c => selected.includes(c.id));

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

      {/* Wager Section */}
      {selected.length >= 2 && (
        <div className="card mt-12" style={{ borderColor: 'var(--warning)' }}>
          <div className="flex flex-between flex-center">
            <strong style={{ color: 'var(--warning)' }}>Wager (Optional)</strong>
            <button
              className="btn btn-sm"
              onClick={() => setWagerEnabled(!wagerEnabled)}
            >
              {wagerEnabled ? 'Disable' : 'Enable'}
            </button>
          </div>

          {wagerEnabled && (
            <div style={{ marginTop: 12 }}>
              {!matchId && (
                <button className="btn btn-sm mb-12" onClick={handleCreateMatch}>
                  Create Match to Place Wager
                </button>
              )}

              {matchId && !wagerPlaced && (
                <>
                  <div className="mb-12">
                    <label style={{ display: 'block', fontSize: '0.85em', color: 'var(--text-dim)', marginBottom: 4 }}>
                      Bet on champion:
                    </label>
                    <select
                      value={wagerChampion}
                      onChange={e => setWagerChampion(e.target.value)}
                      className="input"
                      style={{ width: '100%' }}
                    >
                      <option value="">Select champion...</option>
                      {selectedChampions.map(c => (
                        <option key={c.id} value={c.id}>{c.name} ({c.archetype})</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-12">
                    <label style={{ display: 'block', fontSize: '0.85em', color: 'var(--text-dim)', marginBottom: 4 }}>
                      Amount (SOL):
                    </label>
                    <input
                      type="number"
                      value={wagerAmount}
                      onChange={e => setWagerAmount(e.target.value)}
                      className="input"
                      min="0.01"
                      max="100"
                      step="0.01"
                      style={{ width: '100%' }}
                    />
                  </div>
                  <button
                    className="btn"
                    onClick={handlePlaceWager}
                    disabled={!wagerChampion || !wagerAmount}
                    style={{ width: '100%' }}
                  >
                    Place Wager ({wagerAmount} SOL)
                  </button>
                </>
              )}

              {wagerPlaced && (
                <div style={{ color: 'var(--success)', marginTop: 8 }}>
                  Wager placed! {wagerAmount} SOL on {selectedChampions.find(c => c.id === wagerChampion)?.name || 'champion'}.
                </div>
              )}

              {odds && odds.odds_by_champion && Object.keys(odds.odds_by_champion).length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: '0.85em', color: 'var(--text-dim)', marginBottom: 4 }}>Current Odds:</div>
                  {Object.values(odds.odds_by_champion).map(o => (
                    <div key={o.champion_id} className="stat-row">
                      <span className="stat-label">
                        {selectedChampions.find(c => c.id === o.champion_id)?.name || o.champion_id.slice(0, 8)}
                      </span>
                      <span className="stat-value">
                        {o.total_wagered} SOL ({o.wager_count} bet{o.wager_count !== 1 ? 's' : ''}) — {o.implied_odds}x
                      </span>
                    </div>
                  ))}
                  <div className="stat-row" style={{ borderTop: '1px solid var(--border)', paddingTop: 4, marginTop: 4 }}>
                    <span className="stat-label">Total Pot</span>
                    <span className="stat-value" style={{ color: 'var(--warning)' }}>{odds.total_pot} SOL</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

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
