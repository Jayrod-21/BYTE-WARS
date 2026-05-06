import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { getUser, logout, getWalletBalance } from './services/api';
import { SolDiamond } from './ui/primitives';
import LoginPage from './pages/LoginPage';
import ChampionsPage from './pages/ChampionsPage';
import ChampionBuilderPage from './pages/ChampionBuilderPage';
import MatchLobbyPage from './pages/MatchLobbyPage';
import MatchHistoryPage from './pages/MatchHistoryPage';
import PlaybackPage from './pages/PlaybackPage';
import ProfilePage from './pages/ProfilePage';
import InventoryPage from './pages/InventoryPage';
import WagerHistoryPage from './pages/WagerHistoryPage';
import MarketplacePage from './pages/MarketplacePage';
import SocialPage from './pages/SocialPage';
import ClansPage from './pages/ClansPage';

const TABS = [
  { to: '/lobby', label: 'HOME',   icon: '◆' },
  { to: '/champions', label: 'BUILD', icon: '⚔' },
  { to: '/inventory', label: 'BAG',  icon: '▣' },
  { to: '/marketplace', label: 'SHOP', icon: '◇' },
  { to: '/social', label: 'SOCIAL', icon: '◈' },
];

function HeaderBar({ user, onLogout }) {
  const [balance, setBalance] = useState(null);
  useEffect(() => {
    if (!user) { setBalance(null); return; }
    const wallet = user.wallet_address || `devnet_${user.id || 'anon'}`;
    let cancelled = false;
    getWalletBalance(wallet)
      .then(b => { if (!cancelled) setBalance(b?.balance_sol ?? b?.balance ?? 0); })
      .catch(() => { if (!cancelled) setBalance(0); });
    return () => { cancelled = true; };
  }, [user]);

  return (
    <header style={{
      height: 60,
      background: '#000',
      borderBottom: '2px solid var(--bw-line)',
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
      position: 'sticky',
      top: 0,
      zIndex: 20,
    }}>
      <NavLink to={user ? '/lobby' : '/login'} style={{
        fontFamily: 'var(--font-pixel)',
        fontSize: 14,
        color: 'var(--bw-acid)',
        letterSpacing: '0.08em',
        textShadow: '2px 2px 0 #1d3300',
      }}>
        BYTE WARS
      </NavLink>

      {user ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--bw-yellow)',
            background: 'var(--bw-bg-2)', padding: '6px 10px',
            boxShadow: 'inset 2px 2px 0 0 #000, inset -2px -2px 0 0 var(--bw-line)',
          }}>
            <SolDiamond />
            {balance == null ? '…' : Number(balance).toFixed(2)}
            <span style={{ color: 'var(--bw-ink-low)', fontSize: 9 }}>SOL</span>
          </span>
          <NavLink to="/profile" style={{
            fontFamily: 'var(--font-pixel)', fontSize: 9, color: 'var(--bw-ink)',
            letterSpacing: '0.06em', textTransform: 'uppercase',
          }}>
            {user.username}
          </NavLink>
          <button onClick={onLogout} className="pxbtn pxbtn-ghost" style={{ padding: '6px 10px', fontSize: 8 }}>
            EXIT
          </button>
        </div>
      ) : (
        <NavLink to="/login" className="pxbtn pxbtn-acid" style={{ padding: '8px 14px', fontSize: 9, textDecoration: 'none' }}>
          LOG IN
        </NavLink>
      )}
    </header>
  );
}

function BottomTabs() {
  return (
    <nav style={{
      position: 'fixed',
      bottom: 0, left: 0, right: 0,
      height: 72,
      background: '#000',
      borderTop: '2px solid var(--bw-line)',
      display: 'flex',
      zIndex: 15,
      boxShadow: '0 -4px 0 0 rgba(0,0,0,0.6)',
    }}>
      {TABS.map(tab => (
        <NavLink
          key={tab.to}
          to={tab.to}
          style={({ isActive }) => ({
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            fontFamily: 'var(--font-pixel)',
            fontSize: 7,
            letterSpacing: '0.1em',
            color: isActive ? 'var(--bw-acid)' : 'var(--bw-ink-low)',
            textDecoration: 'none',
            borderTop: isActive ? '3px solid var(--bw-acid)' : '3px solid transparent',
            background: isActive ? 'rgba(182,255,60,0.05)' : 'transparent',
          })}
        >
          <span style={{ fontSize: 18, lineHeight: 1 }}>{tab.icon}</span>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}

function AppContent() {
  const [user, setUser] = useState(getUser());
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    setUser(null);
    navigate('/login');
  }

  function handleLogin(userData) {
    setUser(userData);
    navigate('/lobby');
  }

  const hideChrome = location.pathname === '/login';

  return (
    <>
      {!hideChrome && <HeaderBar user={user} onLogout={handleLogout} />}
      <main className="bw-page" style={{ flex: 1 }}>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="/champions" element={<ChampionsPage />} />
          <Route path="/champions/new" element={<ChampionBuilderPage />} />
          <Route path="/champions/:id/edit" element={<ChampionBuilderPage />} />
          <Route path="/lobby" element={<MatchLobbyPage />} />
          <Route path="/history" element={<MatchHistoryPage />} />
          <Route path="/playback/:matchId" element={<PlaybackPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/marketplace" element={<MarketplacePage />} />
          <Route path="/wagers" element={<WagerHistoryPage />} />
          <Route path="/social" element={<SocialPage />} />
          <Route path="/clans" element={<ClansPage />} />
          <Route path="/profile" element={<ProfilePage user={user} />} />
          <Route path="/" element={<Navigate to={user ? '/lobby' : '/login'} replace />} />
        </Routes>
      </main>
      {!hideChrome && user && <BottomTabs />}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
