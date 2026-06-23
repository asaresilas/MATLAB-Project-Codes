import { useState, useCallback, useRef } from 'react'
import { appConfig } from '../config/appConfig.js'
import { useToast } from '../context/ToastContext.jsx'

/* ── Account management helpers ── */
async function apiPost(path, formData, token) {
  const res = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(json.detail || `Request failed (${res.status})`)
  return json
}

function AccountCard({ session, onLogout }) {
  const [pwForm, setPwForm]     = useState({ current: '', next: '', confirm: '' })
  const [unForm, setUnForm]     = useState({ newUsername: '', confirm_pw: '' })
  const [pwStatus, setPwStatus] = useState(null)   // { ok, msg }
  const [unStatus, setUnStatus] = useState(null)
  const [pwBusy,   setPwBusy]   = useState(false)
  const [unBusy,   setUnBusy]   = useState(false)
  const [tab,      setTab]      = useState('password')   // 'password' | 'username'

  const handlePwChange = async (e) => {
    e.preventDefault()
    if (pwForm.next !== pwForm.confirm) {
      setPwStatus({ ok: false, msg: 'New passwords do not match.' })
      return
    }
    if (pwForm.next.length < 8) {
      setPwStatus({ ok: false, msg: 'New password must be at least 8 characters.' })
      return
    }
    setPwBusy(true)
    setPwStatus(null)
    try {
      const fd = new URLSearchParams({
        current_password: pwForm.current,
        new_password:     pwForm.next,
      })
      const res = await apiPost('/api/v1/auth/change-password', fd, session?.token)
      setPwStatus({ ok: true, msg: res.message || 'Password changed successfully.' })
      setPwForm({ current: '', next: '', confirm: '' })
    } catch (err) {
      setPwStatus({ ok: false, msg: err.message })
    } finally {
      setPwBusy(false)
    }
  }

  const handleUnChange = async (e) => {
    e.preventDefault()
    if (!unForm.newUsername.trim()) {
      setUnStatus({ ok: false, msg: 'Please enter a new username.' })
      return
    }
    setUnBusy(true)
    setUnStatus(null)
    try {
      const fd = new URLSearchParams({
        new_username:     unForm.newUsername.trim(),
        current_password: unForm.confirm_pw,
      })
      const res = await apiPost('/api/v1/auth/change-username', fd, session?.token)
      setUnStatus({ ok: true, msg: (res.message || 'Username changed.') + ' You will be signed out.' })
      setUnForm({ newUsername: '', confirm_pw: '' })
      setTimeout(() => onLogout?.(), 2500)
    } catch (err) {
      setUnStatus({ ok: false, msg: err.message })
    } finally {
      setUnBusy(false)
    }
  }

  const initials = (session?.displayName || session?.username || 'U')
    .split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-header">
        <span className="card-title">Account</span>
        <span style={{ fontSize: 10, color: 'var(--txt-3)', textTransform: 'capitalize' }}>
          {session?.role || 'operator'}
        </span>
      </div>

      {/* Profile strip */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: 'var(--accent-dim)', border: '2px solid var(--accent-glow)',
          color: 'var(--accent)', fontSize: 20, fontWeight: 700,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          {initials}
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--txt)' }}>
            {session?.displayName || session?.username || '—'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--txt-3)', marginTop: 2 }}>
            @{session?.username} &nbsp;·&nbsp; Role:&nbsp;
            <span style={{ color: 'var(--accent)', textTransform: 'capitalize' }}>{session?.role}</span>
          </div>
        </div>
      </div>

      {/* Tab selector */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        {[['password', 'Change Password'], ['username', 'Change Username']].map(([id, label]) => (
          <button
            key={id}
            onClick={() => { setTab(id); setPwStatus(null); setUnStatus(null) }}
            style={{
              padding: '10px 20px',
              background: 'none',
              border: 'none',
              borderBottom: tab === id ? '2px solid var(--accent)' : '2px solid transparent',
              color: tab === id ? 'var(--accent)' : 'var(--txt-3)',
              fontWeight: tab === id ? 700 : 500,
              fontSize: 13,
              cursor: 'pointer',
              marginBottom: -1,
              transition: 'color 0.15s',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={{ padding: '20px', maxWidth: 420 }}>
        {tab === 'password' && (
          <form onSubmit={handlePwChange} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="field-group">
              <label className="field-label">Current password</label>
              <input
                className="field-input"
                type="password"
                autoComplete="current-password"
                value={pwForm.current}
                onChange={(e) => setPwForm((p) => ({ ...p, current: e.target.value }))}
                required
                disabled={pwBusy}
                placeholder="Enter current password"
              />
            </div>
            <div className="field-group">
              <label className="field-label">New password</label>
              <input
                className="field-input"
                type="password"
                autoComplete="new-password"
                value={pwForm.next}
                onChange={(e) => setPwForm((p) => ({ ...p, next: e.target.value }))}
                required
                disabled={pwBusy}
                placeholder="Min. 8 characters"
              />
            </div>
            <div className="field-group">
              <label className="field-label">Confirm new password</label>
              <input
                className="field-input"
                type="password"
                autoComplete="new-password"
                value={pwForm.confirm}
                onChange={(e) => setPwForm((p) => ({ ...p, confirm: e.target.value }))}
                required
                disabled={pwBusy}
                placeholder="Repeat new password"
              />
            </div>

            {pwStatus && (
              <div style={{
                padding: '9px 12px',
                borderRadius: 'var(--r)',
                fontSize: 12.5,
                background: pwStatus.ok ? 'var(--ok-dim)' : 'var(--crit-dim)',
                border: `1px solid ${pwStatus.ok ? 'var(--ok-border)' : 'var(--crit-border)'}`,
                color: pwStatus.ok ? 'var(--ok)' : 'var(--crit)',
              }}>
                {pwStatus.msg}
              </div>
            )}

            <button className="btn btn-primary" type="submit" disabled={pwBusy} style={{ alignSelf: 'flex-start', padding: '9px 24px' }}>
              {pwBusy ? 'Saving…' : 'Change Password'}
            </button>
          </form>
        )}

        {tab === 'username' && (
          <form onSubmit={handleUnChange} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ padding: '10px 12px', background: 'var(--warn-dim)', border: '1px solid var(--warn-border)', borderRadius: 'var(--r)', fontSize: 12, color: 'var(--warn)' }}>
              Changing your username will sign you out immediately.
            </div>
            <div className="field-group">
              <label className="field-label">New username</label>
              <input
                className="field-input"
                type="text"
                autoComplete="username"
                value={unForm.newUsername}
                onChange={(e) => setUnForm((p) => ({ ...p, newUsername: e.target.value }))}
                required
                disabled={unBusy}
                placeholder="At least 3 characters"
              />
            </div>
            <div className="field-group">
              <label className="field-label">Current password (to confirm)</label>
              <input
                className="field-input"
                type="password"
                autoComplete="current-password"
                value={unForm.confirm_pw}
                onChange={(e) => setUnForm((p) => ({ ...p, confirm_pw: e.target.value }))}
                required
                disabled={unBusy}
                placeholder="Enter your current password"
              />
            </div>

            {unStatus && (
              <div style={{
                padding: '9px 12px',
                borderRadius: 'var(--r)',
                fontSize: 12.5,
                background: unStatus.ok ? 'var(--ok-dim)' : 'var(--crit-dim)',
                border: `1px solid ${unStatus.ok ? 'var(--ok-border)' : 'var(--crit-border)'}`,
                color: unStatus.ok ? 'var(--ok)' : 'var(--crit)',
              }}>
                {unStatus.msg}
              </div>
            )}

            <button className="btn btn-primary" type="submit" disabled={unBusy} style={{ alignSelf: 'flex-start', padding: '9px 24px' }}>
              {unBusy ? 'Saving…' : 'Change Username'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

/* Default settings for Reset to Defaults */
const DEFAULT_SETTINGS = {
  alertCritical: true,
  alertWarning:  false,
  soundAlerts:   false,
  trendWindow:   '15m',
  updateRate:    '1000',
  exportFormat:  'pdf',
  vibWarn:       5,
  vibCrit:       8,
  tempWarn:      75,
  tempCrit:      90,
  rulAlert:      100,
}

/* Validation rules for threshold fields */
function validateThresholds(local) {
  const errs = []
  if (Number(local.vibWarn) >= Number(local.vibCrit))   errs.push('Vibration warning must be less than critical threshold.')
  if (Number(local.tempWarn) >= Number(local.tempCrit)) errs.push('Temperature warning must be less than critical threshold.')
  if (Number(local.vibWarn)  <= 0) errs.push('Vibration warning must be greater than 0.')
  if (Number(local.rulAlert) <= 0) errs.push('RUL alert threshold must be greater than 0.')
  return errs
}

export function SettingsPage({ controller }) {
  const { settings, updateSettings, session, logout } = controller
  const isEngineer = session?.role === 'engineer' || session?.role === 'admin'
  const { push: pushToast } = useToast()

  const [local,        setLocal]        = useState(settings ?? {})
  const [threshErrors, setThreshErrors] = useState([])
  const [connTesting,  setConnTesting]  = useState(false)
  const [connResult,   setConnResult]   = useState(null)   // null | { ok, msg }
  const saveTimerRef = useRef(null)

  /* Debounced save with toast — called after every change */
  const saveWithFeedback = useCallback((next, label) => {
    if (updateSettings) updateSettings(next)
    clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      pushToast({ title: 'Settings saved', message: label ?? 'Your changes have been applied.', type: 'ok', duration: 2500 })
    }, 600)
  }, [updateSettings, pushToast])

  const set = (key) => (e) => {
    const val  = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    const next = { ...local, [key]: val }
    setLocal(next)
    // Validate thresholds on every threshold change
    const errs = validateThresholds(next)
    setThreshErrors(errs)
    if (errs.length === 0) saveWithFeedback(next)
  }

  const toggle = (key) => () => {
    const next = { ...local, [key]: !local[key] }
    setLocal(next)
    saveWithFeedback(next, `${key.replace(/([A-Z])/g, ' $1').trim()} ${next[key] ? 'enabled' : 'disabled'}.`)
  }

  const resetToDefaults = () => {
    setLocal(DEFAULT_SETTINGS)
    setThreshErrors([])
    if (updateSettings) updateSettings(DEFAULT_SETTINGS)
    pushToast({ title: 'Settings reset', message: 'All settings restored to factory defaults.', type: 'ok', duration: 3000 })
  }

  const testConnection = async () => {
    setConnTesting(true)
    setConnResult(null)
    try {
      const start = Date.now()
      const res   = await fetch(`${appConfig.apiBaseUrl}/health`, { signal: AbortSignal.timeout(5000) })
      const ms    = Date.now() - start
      if (res.ok) {
        setConnResult({ ok: true, msg: `Connected — response time ${ms} ms` })
      } else {
        setConnResult({ ok: false, msg: `Server responded with status ${res.status}` })
      }
    } catch (err) {
      setConnResult({ ok: false, msg: `Connection failed: ${err.message}` })
    } finally {
      setConnTesting(false)
    }
  }

  return (
    <div className="settings-page-shell">
      <div className="page-header">
        <div>
          <div className="page-title">Settings</div>
          <div className="page-sub">System configuration and preferences</div>
        </div>
        <span style={{ fontSize: 11, padding: '4px 10px', borderRadius: '999px', background: 'var(--bg-raised)', color: 'var(--txt-3)', fontWeight: 600, textTransform: 'capitalize' }}>
          {session?.role || 'operator'}
        </span>
      </div>

      {/* ── Threshold validation errors ── */}
      {threshErrors.length > 0 && (
        <div style={{ margin: '0 0 16px', padding: '10px 14px', background: 'var(--crit-dim)', border: '1px solid var(--crit-border)', borderRadius: 'var(--r)', fontSize: 12.5, color: 'var(--crit)' }}>
          <strong>Threshold configuration error:</strong>
          <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>
            {threshErrors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}

      <div className="settings-grid">
        {/* Account — change password / username */}
        <AccountCard session={session} onLogout={logout} />

        {/* Notification settings */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Notifications</span>
          </div>
          <div className="card-body">
            <div className="toggle-row">
              <div className="toggle-info">
                <div className="toggle-name">Critical alarms</div>
                <div className="toggle-desc">Alert on critical fault detection</div>
              </div>
              <div
                className={`toggle ${local.alertCritical !== false ? 'on' : ''}`}
                onClick={toggle('alertCritical')}
                role="switch"
                aria-checked={local.alertCritical !== false}
              />
            </div>
            <div className="toggle-row">
              <div className="toggle-info">
                <div className="toggle-name">Warning alarms</div>
                <div className="toggle-desc">Alert on warning-level events</div>
              </div>
              <div
                className={`toggle ${local.alertWarning ? 'on' : ''}`}
                onClick={toggle('alertWarning')}
                role="switch"
                aria-checked={!!local.alertWarning}
              />
            </div>
            <div className="toggle-row">
              <div className="toggle-info">
                <div className="toggle-name">Sound alerts</div>
                <div className="toggle-desc">Audible notification on new alarms</div>
              </div>
              <div
                className={`toggle ${local.soundAlerts ? 'on' : ''}`}
                onClick={toggle('soundAlerts')}
                role="switch"
                aria-checked={!!local.soundAlerts}
              />
            </div>
          </div>
        </div>

        {/* Display settings */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Display</span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="field-group">
              <label className="field-label">Trend window</label>
              <select className="field-select" value={local.trendWindow || '15m'} onChange={set('trendWindow')}>
                <option value="5m">5 minutes</option>
                <option value="15m">15 minutes</option>
                <option value="1h">1 hour</option>
                <option value="6h">6 hours</option>
                <option value="24h">24 hours</option>
              </select>
            </div>
            <div className="field-group">
              <label className="field-label">Update rate</label>
              <select className="field-select" value={local.updateRate || '1000'} onChange={set('updateRate')}>
                <option value="500">500 ms (fast)</option>
                <option value="1000">1 second</option>
                <option value="2000">2 seconds</option>
                <option value="5000">5 seconds</option>
              </select>
            </div>
            <div className="field-group">
              <label className="field-label">Export format</label>
              <select className="field-select" value={local.exportFormat || 'pdf'} onChange={set('exportFormat')}>
                <option value="pdf">PDF report</option>
                <option value="csv">CSV data</option>
                <option value="json">JSON raw</option>
              </select>
            </div>
          </div>
        </div>

        {/* Threshold settings — engineer+ only */}
        {isEngineer && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">Alarm Thresholds</span>
              <span style={{ fontSize: 10, color: 'var(--warn)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Engineer</span>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="field-group">
                <label className="field-label">Vibration warning (g)</label>
                <input className="field-input" type="number" step="0.1" value={local.vibWarn ?? 5} onChange={set('vibWarn')} />
              </div>
              <div className="field-group">
                <label className="field-label">Vibration critical (g)</label>
                <input className="field-input" type="number" step="0.1" value={local.vibCrit ?? 8} onChange={set('vibCrit')} />
              </div>
              <div className="field-group">
                <label className="field-label">Temperature warning (°C)</label>
                <input className="field-input" type="number" step="1" value={local.tempWarn ?? 75} onChange={set('tempWarn')} />
              </div>
              <div className="field-group">
                <label className="field-label">Temperature critical (°C)</label>
                <input className="field-input" type="number" step="1" value={local.tempCrit ?? 90} onChange={set('tempCrit')} />
              </div>
              <div className="field-group">
                <label className="field-label">RUL alert threshold (h)</label>
                <input className="field-input" type="number" step="10" min="1" max="500" value={local.rulAlert ?? 100} onChange={set('rulAlert')} />
                <span className="field-hint">Alarm triggers when RUL drops below this value</span>
              </div>
              <button
                className="btn btn-ghost"
                style={{ alignSelf: 'flex-start', marginTop: 4, fontSize: 12 }}
                onClick={resetToDefaults}
                type="button"
              >
                ↺ Reset all to defaults
              </button>
            </div>
          </div>
        )}

        {/* Connection */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Connection</span>
          </div>
          <div className="card-body">
            <div className="param-table">
              {[
                ['API endpoint', appConfig.apiBaseUrl || 'http://127.0.0.1:8000'],
                ['WebSocket',    'ws://127.0.0.1:8000/ws/dashboard'],
                ['Protocol',     'WebSocket + REST/HTTP'],
                ['Auth',         'JWT Bearer token'],
              ].map(([k, v]) => (
                <div key={k} className="param-row">
                  <span className="param-key">{k}</span>
                  <span className="param-val mono" style={{ fontSize: 11.5, color: 'var(--txt-2)' }}>{v}</span>
                </div>
              ))}
            </div>

            {/* Connection test */}
            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                className="btn btn-ghost"
                style={{ alignSelf: 'flex-start', fontSize: 12.5 }}
                onClick={testConnection}
                disabled={connTesting}
                type="button"
              >
                {connTesting ? '⟳ Testing…' : '⚡ Test Connection'}
              </button>
              {connResult && (
                <div style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--r)',
                  fontSize: 12,
                  background: connResult.ok ? 'var(--ok-dim)' : 'var(--crit-dim)',
                  border: `1px solid ${connResult.ok ? 'var(--ok-border)' : 'var(--crit-border)'}`,
                  color: connResult.ok ? 'var(--ok)' : 'var(--crit)',
                  fontFamily: 'var(--mono)',
                }}>
                  {connResult.ok ? '✓ ' : '✗ '}{connResult.msg}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
