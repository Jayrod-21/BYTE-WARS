import { useState } from 'react';
import { register, login } from '../services/api';

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = isRegister
        ? await register(username, password)
        : await login(username, password);
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '60px auto' }}>
      <h1 className="page-title">{isRegister ? 'Create Account' : 'Login'}</h1>
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Enter username"
            required
            minLength={3}
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Enter password"
            required
            minLength={6}
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="btn" disabled={loading} style={{ width: '100%', marginTop: 12 }}>
          {loading ? 'Loading...' : isRegister ? 'Register' : 'Login'}
        </button>
      </form>
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <button
          className="nav-btn"
          onClick={() => { setIsRegister(!isRegister); setError(''); }}
        >
          {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
        </button>
      </div>
    </div>
  );
}
