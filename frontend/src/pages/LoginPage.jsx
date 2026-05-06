import { useState } from 'react';
import { register, login } from '../services/api';
import { PixelButton, Sprite } from '../ui/primitives';

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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16,
      background: 'radial-gradient(ellipse at center, #11111c 0%, #0a0a12 70%)',
    }}>
      <div className="panel scanlines" style={{ width: '100%', maxWidth: 420, padding: 24 }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{
            fontFamily: 'var(--font-pixel)',
            fontSize: 22,
            color: 'var(--bw-acid)',
            letterSpacing: '0.1em',
            textShadow: '3px 3px 0 #1d3300',
            marginBottom: 8,
          }}>
            BYTE WARS
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--bw-ink-dim)',
            letterSpacing: '0.05em',
          }}>
            AI BATTLE COLISEUM <span className="blink">_</span>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 20 }}>
          <Sprite kind="tank" scale={3} />
          <Sprite kind="mage" scale={3} />
          <Sprite kind="assassin" scale={3} />
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 14 }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-pixel)',
              fontSize: 8,
              letterSpacing: '0.1em',
              color: 'var(--bw-ink-dim)',
              marginBottom: 6,
              textTransform: 'uppercase',
            }}>
              {'>'} CALLSIGN
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="enter callsign"
              required
              minLength={3}
              autoComplete="username"
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-pixel)',
              fontSize: 8,
              letterSpacing: '0.1em',
              color: 'var(--bw-ink-dim)',
              marginBottom: 6,
              textTransform: 'uppercase',
            }}>
              {'>'} PASSCODE
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              style={{ width: '100%' }}
            />
          </div>

          {error && (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--bw-blood)',
              marginBottom: 12,
              padding: '8px 10px',
              background: 'rgba(255,60,92,0.08)',
              boxShadow: 'inset 0 0 0 2px var(--bw-blood)',
            }}>
              ! {error}
            </div>
          )}

          <PixelButton variant="acid" type="submit" full disabled={loading}>
            {loading ? 'CONNECTING…' : isRegister ? 'JOIN ARENA' : 'ENTER ARENA'}
          </PixelButton>
        </form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            type="button"
            onClick={() => { setIsRegister(!isRegister); setError(''); }}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--bw-cyan)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: 4,
            }}
          >
            {isRegister ? 'have an account? log in' : 'new fighter? register'}
          </button>
        </div>
      </div>
    </div>
  );
}
