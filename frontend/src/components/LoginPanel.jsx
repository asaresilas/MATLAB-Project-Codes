import { useState, useEffect } from 'react'
import { appConfig } from '../config/appConfig.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

/**
 * Poll /health to show a live backend status dot.
 * Fast (2 s) while offline so the dot turns green quickly.
 * Slow (15 s) once online — no need to hammer the server.
 */
function useBackendStatus() {
  const [status, setStatus] = useState('checking') // 'checking' | 'online' | 'offline'

  useEffect(() => {
    let cancelled = false

    async function check() {
      try {
        const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' })
        if (!cancelled) setStatus(res.ok ? 'online' : 'offline')
      } catch {
        if (!cancelled) setStatus('offline')
      }
    }

    // Kick off the first check immediately, then use a self-adjusting loop
    // so the interval matches the current online/offline state.
    let id
    async function loop() {
      await check()
      if (cancelled) return
      setStatus((current) => {
        const delay = current === 'online' ? 15000 : 2000
        id = setTimeout(loop, delay)
        return current
      })
    }

    loop()
    return () => { cancelled = true; clearTimeout(id) }
  }, [])

  return status
}

export function LoginPanel({ onLogin, error, isAuthenticating, onSetup }) {
  const [form, setForm]         = useState({ username: '', password: '' })
  const [showPassword, setShow] = useState(false)
  const backendStatus           = useBackendStatus()

  const handleChange = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!isAuthenticating) onLogin(form)
  }

  return (
    <div className="login-shell">
      <div className="login-panel">
        <div className="login-logo-row">
          <div className="login-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M2 12h4M18 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div className="login-eyebrow">Secure console access</div>
            <div className="login-title">MotorGuard Digital Twin</div>
          </div>
          {/* Backend status indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--txt-3)', flexShrink: 0 }}>
            <span style={{
              display: 'inline-block',
              width: 8, height: 8,
              borderRadius: '50%',
              background: backendStatus === 'online' ? '#22c55e' : backendStatus === 'offline' ? '#ef4444' : '#f59e0b',
              boxShadow: backendStatus === 'online' ? '0 0 6px #22c55e99' : backendStatus === 'offline' ? '0 0 6px #ef444499' : '0 0 6px #f59e0b99',
            }} />
            <span>
              {backendStatus === 'online' ? 'Backend online' : backendStatus === 'offline' ? 'Backend offline' : 'Checking…'}
            </span>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit} autoComplete="on">
          <div>
            <h2>Sign in</h2>
            <p>Use your operator, engineer, or administrator credentials.</p>
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              className="field-input"
              type="text"
              name="username"
              autoComplete="username"
              value={form.username}
              onChange={handleChange('username')}
              disabled={isAuthenticating}
              required
              placeholder="Enter username"
            />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="login-password">Password</label>
            <div className="field-password-wrap">
              <input
                id="login-password"
                className="field-input"
                type={showPassword ? 'text' : 'password'}
                name="password"
                autoComplete="current-password"
                value={form.password}
                onChange={handleChange('password')}
                disabled={isAuthenticating}
                required
                placeholder="Enter password"
              />
              <button
                type="button"
                className="field-password-toggle"
                onClick={() => setShow((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={0}
              >
                {showPassword
                  ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                }
              </button>
            </div>
          </div>

          {/* Offline warning — shown before user even tries to log in */}
          {backendStatus === 'offline' && !error && (
            <div className="error-banner" role="alert" style={{ background: 'rgba(239,68,68,0.12)', borderColor: 'rgba(239,68,68,0.35)' }}>
              <strong>Backend server is not running.</strong>
              <br />
              Open a terminal in the <code>backend/</code> folder and run:
              <br />
              <code style={{ display: 'block', marginTop: 4 }}>python run.py</code>
            </div>
          )}

          {/* Auth error from login attempt */}
          {error && (
            <div className="error-banner" role="alert">
              {error}
              {error.includes('Cannot reach') && (
                <div style={{ marginTop: 6, fontSize: 11, opacity: 0.85 }}>
                  Start the backend: in the <code>backend/</code> folder run <code>python run.py</code>
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={isAuthenticating || backendStatus === 'offline'}
            title={backendStatus === 'offline' ? 'Start the backend server first' : ''}
          >
            {isAuthenticating ? 'Signing in…' : backendStatus === 'offline' ? 'Backend offline — cannot sign in' : 'Open Console'}
          </button>
        </form>

        {onSetup && (
          <div style={{ textAlign: 'center', marginTop: 4 }}>
            <button
              type="button"
              onClick={onSetup}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--accent)', textDecoration: 'underline', padding: 0 }}
            >
              First-time setup? Create accounts
            </button>
          </div>
        )}

        <div className="login-machine">
          <span className="login-machine-label">Machine</span>
          <span className="login-machine-id">{appConfig.machineId}</span>
        </div>
      </div>
    </div>
  )
}
