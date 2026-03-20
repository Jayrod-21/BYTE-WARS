import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import { getUser, logout } from './services/api';
import LoginPage from './pages/LoginPage';
import ChampionsPage from './pages/ChampionsPage';
import ChampionBuilderPage from './pages/ChampionBuilderPage';
import MatchLobbyPage from './pages/MatchLobbyPage';
import MatchHistoryPage from './pages/MatchHistoryPage';
import PlaybackPage from './pages/PlaybackPage';
import ProfilePage from './pages/ProfilePage';
import InventoryPage from './pages/InventoryPage';
import WagerHistoryPage from './pages/WagerHistoryPage';
import './App.css';

function NavBar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">BYTE WARS</Link>
      <div className="nav-links">
        <Link to="/champions">Champions</Link>
        <Link to="/lobby">Battle</Link>
        <Link to="/inventory">Inventory</Link>
        <Link to="/wagers">Wagers</Link>
        <Link to="/history">History</Link>
        {user ? (
          <>
            <Link to="/profile">{user.username}</Link>
            <button onClick={onLogout} className="nav-btn">Logout</button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
}

function AppContent() {
  const [user, setUser] = useState(getUser());
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    setUser(null);
    navigate('/login');
  }

  function handleLogin(userData) {
    setUser(userData);
    navigate('/champions');
  }

  return (
    <>
      <NavBar user={user} onLogout={handleLogout} />
      <main className="main-content">
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="/champions" element={<ChampionsPage />} />
          <Route path="/champions/new" element={<ChampionBuilderPage />} />
          <Route path="/lobby" element={<MatchLobbyPage />} />
          <Route path="/history" element={<MatchHistoryPage />} />
          <Route path="/playback/:matchId" element={<PlaybackPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/wagers" element={<WagerHistoryPage />} />
          <Route path="/profile" element={<ProfilePage user={user} />} />
          <Route path="/" element={<Navigate to="/champions" />} />
        </Routes>
      </main>
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
