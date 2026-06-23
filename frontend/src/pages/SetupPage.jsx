import { useState } from 'react'
import { appConfig } from '../config/appConfig.js'
import { submitSetup } from '../services/authService.js'

const STEPS = ['admin', 'engineer', 'confirm']

function ProgressBar({ step }) {
  const labels = ['Admin Account', 'Engineer Account', 'Confirm']
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 28 }}>
      {labels.map((label, i) => {
        const active   = i === step
        const complete = i < step
        return (
          <div key={label} style={{ display: 'flex', alignItems: 'center', flex: i < labels.length - 1 ? 1 : 'none' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: complete ? 'var(--ok)' : active ? 'var(--accent)' : 'var(--bg-raised)',
                border: `2px solid ${complete ? 'var(--ok)' : active ? 'var(--accent)' : 'var(--border-md)'}`,
                color: (complete || active) ? '#fff' : 'var(--txt-3)',
                fontSize: 12, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.2s',
              }}>
                {complete ? '✓' : i + 1}
              </div>
              <span style={{ fontSize: 10, color: active ? 'var(--accent)' : complete ? 'var(--ok)' : 'var(--txt-3)', whiteSpace: 'nowrap', fontWeight: active ? 700 : 400 }}>
                {label}
              </span>
            </div>
            {i < labels.length - 1 && (
              <div style={{ flex: 1, height: 2, background: complete ? 'var(--ok)' : 'var(--border)', margin: '0 6px', marginBottom: 20, transition: 'background 0.3s' }} />
            )}
          </div>
        )
      })}
    </div>
  )
}

function PasswordStrength({ password }) {
  if (!password) return null
  const checks = [
    { label: '8+ characters',       pass: password.length >= 8 },
    { label: 'Uppercase letter',     pass: /[A-Z]/.test(password) },
    { label: 'Lowercase letter',     pass: /[a-z]/.test(password) },
    { label: 'Number',               pass: /\d/.test(password) },
    { label: 'Special character',    pass: /[^A-Za-z0-9]/.test(password) },
  ]
  const score = checks.filter((c) => c.pass).length
  const color = score < 2 ? 'var(--crit)' : score < 4 ? 'var(--warn)' : 'var(--ok)'
  const label = score < 2 ? 'Weak' : score < 4 ? 'Fair' : score === 5 ? 'Strong' : 'Good'

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {checks.map((_, i) => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i < score ? color : 'var(--bg-raised)', transition: 'background 0.2s' }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 4 }}>
        {checks.map((c) => (
          <span key={c.label} style={{ fontSize: 10, color: c.pass ? 'var(--ok)' : 'var(--txt-3)' }}>
            {c.pass ? '✓' : '○'} {c.label}
          </span>
        ))}
        <span style={{ fontSize: 10, fontWeight: 700, color, marginLeft: 'auto' }}>{label}</span>
      </div>
    </div>
  )
}

export function SetupPage({ onSetupComplete }) {
  const [step, setStep]       = useState(0)
  const [busy, setBusy]       = useState(false)
  const [error, setError]     = useState('')
  const [skipEng, setSkipEng] = useState(false)

  const [admin, setAdmin] = useState({
    username: '', password: '', confirm: '', fullName: '',
  })
  const [eng, setEng] = useState({
    username: '', password: '', confirm: '', fullName: '',
  })

  const setA = (k) => (e) => setAdmin((p) => ({ ...p, [k]: e.target.value }))
  const setE = (k) => (e) => setEng((p)   => ({ ...p, [k]: e.target.value }))

  const validateAdmin = () => {
    if (!admin.username.trim() || admin.username.trim().length < 3)
      return 'Username must be at least 3 characters.'
    if (admin.password.length < 8)
      return 'Password must be at least 8 characters.'
    if (admin.password !== admin.confirm)
      return 'Passwords do not match.'
    return null
  }

  const validateEngineer = () => {
    if (skipEng) return null
    if (!eng.username.trim() || eng.username.trim().length < 3)
      return 'Engineer username must be at least 3 characters.'
    if (eng.password.length < 8)
      return 'Engineer password must be at least 8 characters.'
    if (eng.password !== eng.confirm)
      return 'Engineer passwords do not match.'
    if (eng.username.trim() === admin.username.trim())
      return 'Engineer username must be different from admin username.'
    return null
  }

  const nextStep = () => {
    setError('')
    if (step === 0) {
      const err = validateAdmin()
      if (err) { setError(err); return }
      setStep(1)
    } else if (step === 1) {
      const err = validateEngineer()
      if (err) { setError(err); return }
      setStep(2)
    }
  }

  const handleSubmit = async () => {
    setBusy(true)
    setError('')
    try {
      await submitSetup({
        adminUsername:    admin.username.trim(),
        adminPassword:    admin.password,
        adminFullName:    admin.fullName.trim() || 'System Administrator',
        engineerUsername: skipEng ? '' : eng.username.trim(),
        engineerPassword: skipEng ? '' : eng.password,
        engineerFullName: skipEng ? '' : (eng.fullName.trim() || 'Maintenance Engineer'),
      })
      onSetupComplete()
    } catch (err) {
      setError(err.message)
      setStep(0)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <div style={{ width: 480, background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '36px 36px 32px', boxShadow: '0 20px 60px rgba(0,0,0,0.4)' }}>

        {/* Logo row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div style={{ width: 40, height: 40, background: 'var(--accent)', borderRadius: 'var(--r)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M2 12h4M18 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--txt-3)' }}>First-Time Setup</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--txt)' }}>MotorGuard Digital Twin</div>
          </div>
        </div>

        <p style={{ fontSize: 12.5, color: 'var(--txt-3)', marginBottom: 24, lineHeight: 1.6 }}>
          No accounts exist yet. Create your administrator account to get started. You can add more users later from Settings.
        </p>

        <ProgressBar step={step} />

        {/* ── STEP 0: Admin account ── */}
        {step === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginBottom: 4 }}>
              Administrator Account
            </div>

            <div className="field-group">
              <label className="field-label">Full name <span style={{ color: 'var(--txt-3)', fontWeight: 400 }}>(optional)</span></label>
              <input className="field-input" type="text" placeholder="e.g. Silas Asare" value={admin.fullName} onChange={setA('fullName')} autoFocus />
            </div>

            <div className="field-group">
              <label className="field-label">Username <span style={{ color: 'var(--crit)' }}>*</span></label>
              <input className="field-input" type="text" placeholder="Min. 3 characters" value={admin.username} onChange={setA('username')} autoComplete="username" />
            </div>

            <div className="field-group">
              <label className="field-label">Password <span style={{ color: 'var(--crit)' }}>*</span></label>
              <input className="field-input" type="password" placeholder="Min. 8 characters" value={admin.password} onChange={setA('password')} autoComplete="new-password" />
              <PasswordStrength password={admin.password} />
            </div>

            <div className="field-group">
              <label className="field-label">Confirm password <span style={{ color: 'var(--crit)' }}>*</span></label>
              <input className="field-input" type="password" placeholder="Repeat password" value={admin.confirm} onChange={setA('confirm')} autoComplete="new-password" />
              {admin.confirm && admin.password !== admin.confirm && (
                <span style={{ fontSize: 11, color: 'var(--crit)', marginTop: 4 }}>Passwords do not match</span>
              )}
              {admin.confirm && admin.password === admin.confirm && admin.confirm.length > 0 && (
                <span style={{ fontSize: 11, color: 'var(--ok)', marginTop: 4 }}>✓ Passwords match</span>
              )}
            </div>
          </div>
        )}

        {/* ── STEP 1: Engineer account ── */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#a78bfa', marginBottom: 4 }}>
              Engineer Account <span style={{ fontWeight: 400, color: 'var(--txt-3)' }}>(optional)</span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--txt-3)', marginTop: -8 }}>
              The engineer role can view all pages and adjust alarm thresholds. You can skip this and add it later.
            </p>

            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: 'var(--txt-2)' }}>
              <input type="checkbox" checked={skipEng} onChange={(e) => setSkipEng(e.target.checked)} style={{ accentColor: 'var(--accent)', width: 15, height: 15 }} />
              Skip — add engineer account later
            </label>

            {!skipEng && (
              <>
                <div className="field-group">
                  <label className="field-label">Full name <span style={{ color: 'var(--txt-3)', fontWeight: 400 }}>(optional)</span></label>
                  <input className="field-input" type="text" placeholder="e.g. John Mensah" value={eng.fullName} onChange={setE('fullName')} />
                </div>
                <div className="field-group">
                  <label className="field-label">Username <span style={{ color: 'var(--crit)' }}>*</span></label>
                  <input className="field-input" type="text" placeholder="Min. 3 characters" value={eng.username} onChange={setE('username')} />
                </div>
                <div className="field-group">
                  <label className="field-label">Password <span style={{ color: 'var(--crit)' }}>*</span></label>
                  <input className="field-input" type="password" placeholder="Min. 8 characters" value={eng.password} onChange={setE('password')} />
                  <PasswordStrength password={eng.password} />
                </div>
                <div className="field-group">
                  <label className="field-label">Confirm password <span style={{ color: 'var(--crit)' }}>*</span></label>
                  <input className="field-input" type="password" placeholder="Repeat password" value={eng.confirm} onChange={setE('confirm')} />
                  {eng.confirm && eng.password !== eng.confirm && (
                    <span style={{ fontSize: 11, color: 'var(--crit)', marginTop: 4 }}>Passwords do not match</span>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* ── STEP 2: Confirm ── */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ok)', marginBottom: 4 }}>Review & Confirm</div>

            {[
              { label: 'Admin username', value: admin.username },
              { label: 'Admin name',     value: admin.fullName || 'System Administrator' },
              !skipEng && { label: 'Engineer username', value: eng.username || '—' },
              !skipEng && { label: 'Engineer name',     value: eng.fullName || 'Maintenance Engineer' },
            ].filter(Boolean).map(({ label, value }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: 12, color: 'var(--txt-3)' }}>{label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--txt)', fontFamily: 'var(--mono)' }}>{value}</span>
              </div>
            ))}

            <div style={{ padding: '12px', background: 'var(--ok-dim)', border: '1px solid var(--ok-border)', borderRadius: 'var(--r)', fontSize: 12, color: 'var(--ok)', marginTop: 8 }}>
              Passwords are hashed with PBKDF2-HMAC-SHA256 and stored securely. They are never stored in plain text.
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ marginTop: 14, padding: '9px 12px', background: 'var(--crit-dim)', border: '1px solid var(--crit-border)', borderRadius: 'var(--r)', fontSize: 12.5, color: 'var(--crit)' }}>
            {error}
          </div>
        )}

        {/* Navigation buttons */}
        <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
          {step > 0 && (
            <button className="btn btn-ghost" onClick={() => { setStep(step - 1); setError('') }} disabled={busy}>
              Back
            </button>
          )}
          <div style={{ flex: 1 }} />
          {step < 2 && (
            <button className="btn btn-primary" onClick={nextStep} style={{ padding: '9px 28px' }}>
              Next →
            </button>
          )}
          {step === 2 && (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={busy} style={{ padding: '9px 28px' }}>
              {busy ? 'Creating accounts…' : 'Create Accounts & Sign In →'}
            </button>
          )}
        </div>

        <div style={{ marginTop: 20, textAlign: 'center', fontSize: 11, color: 'var(--txt-3)' }}>
          Machine: <span style={{ fontFamily: 'var(--mono)' }}>{appConfig.machineId}</span>
        </div>
      </div>
    </div>
  )
}
