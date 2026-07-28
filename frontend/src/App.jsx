import { useState, useEffect, useCallback, useRef } from 'react'
import { Navigation }         from './components/Navigation.jsx'
import { TopBar }             from './components/TopBar.jsx'
import { LoginPanel }         from './components/LoginPanel.jsx'
import { KeyboardShortcuts }  from './components/KeyboardShortcuts.jsx'
import { ErrorBoundary }      from './components/ErrorBoundary.jsx'
import { DashboardPage }      from './pages/DashboardPage.jsx'
import { SensorPage }         from './pages/SensorPage.jsx'
import { TrendsPage }         from './pages/TrendsPage.jsx'
import { AlarmsPage }         from './pages/AlarmsPage.jsx'
import { SettingsPage }       from './pages/SettingsPage.jsx'
import { AboutPage }          from './pages/AboutPage.jsx'
import { SetupPage }          from './pages/SetupPage.jsx'
import { ReportPage }         from './pages/ReportPage.jsx'
import DiagnosticsPage        from './pages/DiagnosticsPage.jsx'
import { ThemeProvider, useTheme } from './context/ThemeContext.jsx'
import { ToastProvider, useToast } from './context/ToastContext.jsx'
import { useDashboardController }  from './hooks/useDashboardController.js'
import { useAlarmAudio }           from './hooks/useAlarmAudio.js'
import { checkSetupRequired }      from './services/authService.js'

/* ── Constants ───────────────────────────────────────────────────── */
const PAGE_TITLES = {
  dashboard:   'System Overview',
  sensors:     'Live Sensors',
  diagnostics: 'AI Diagnostics',
  trends:      'Trend Analysis',
  alarms:      'Alarm Center',
  reports:     'Maintenance Report',
  settings:    'Settings',
  about:       'Help & Documentation',
}

const KEY_NAV = { d: 'dashboard', s: 'sensors', i: 'diagnostics', t: 'trends', a: 'alarms', g: 'settings', h: 'about' }

/* Session inactivity timeout — 30 minutes (OSHA/industrial HMI best practice) */
const SESSION_TIMEOUT_MS = 30 * 60 * 1000        // 30 min → auto-logout
const SESSION_WARN_MS    = SESSION_TIMEOUT_MS - 5 * 60 * 1000  // warn at 25 min

/* ── Per-page ErrorBoundary ───────────────────────────────────────── */
function PageErrorBoundary({ children, pageName }) {
  return <ErrorBoundary key={pageName}>{children}</ErrorBoundary>
}

/* ── Loading screen ───────────────────────────────────────────────── */
function LoadingScreen() {
  return (
    <div className="login-shell">
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, color: 'var(--txt-3)' }}>
        <svg
          width="40" height="40" viewBox="0 0 24 24" fill="none"
          stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          style={{ animation: 'spin 1s linear infinite' }}
        >
          <path d="M12 2v4M12 18v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M2 12h4M18 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
        </svg>
        <span style={{ fontSize: 13 }}>Connecting to MotorGuard…</span>
      </div>
    </div>
  )
}

/* ── Inner app (has access to ThemeContext + ToastContext) ───────── */
function AppInner() {
  const controller     = useDashboardController()
  const { toggle: toggleTheme } = useTheme()
  const { push: pushToast }     = useToast()

  const [page,          setPage]          = useState('dashboard')
  const [setupRequired, setSetupRequired] = useState(null)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [sidebarOpen,   setSidebarOpen]   = useState(false)

  /* Alarm audio */
  const healthState = controller.machine?.healthState || 'unknown'
  const rulHours    = controller.machine?.rulHours
  const { muted: alarmMuted, toggleMute: toggleAlarmMute } = useAlarmAudio(healthState)

  /* ── Session inactivity timeout ──────────────────────────────── */
  const lastActivityRef = useRef(Date.now())
  const warnedRef       = useRef(false)

  const resetActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
    warnedRef.current = false
  }, [])

  useEffect(() => {
    if (!controller.session) return   // not logged in — don't track

    const EVENTS = ['mousemove', 'keydown', 'pointerdown', 'scroll']
    EVENTS.forEach((ev) => window.addEventListener(ev, resetActivity, { passive: true }))

    const tick = setInterval(() => {
      const idle = Date.now() - lastActivityRef.current

      if (!warnedRef.current && idle >= SESSION_WARN_MS) {
        warnedRef.current = true
        pushToast({
          title:    'Session expiring',
          message:  'No activity detected — you will be signed out in 5 minutes.',
          type:     'warning',
          duration: 20000,
        })
      }

      if (idle >= SESSION_TIMEOUT_MS) {
        clearInterval(tick)
        pushToast({
          title:   'Session timeout',
          message: 'Signed out due to inactivity.',
          type:    'error',
          duration: 6000,
        })
        controller.logout?.()
      }
    }, 30000)   // check every 30 s

    return () => {
      EVENTS.forEach((ev) => window.removeEventListener(ev, resetActivity))
      clearInterval(tick)
    }
  }, [controller.session, controller.logout, pushToast, resetActivity])

  /* ── Setup check — also handles the case where the backend is down ── */
  useEffect(() => {
    // Cap wait at 4 s so the login page (with offline warning) appears quickly
    const timeout = new Promise((res) => setTimeout(() => res(false), 4000))
    Promise.race([checkSetupRequired(), timeout]).then((required) => setSetupRequired(required))
  }, [])

  /* ── Global keyboard shortcuts ───────────────────────────────── */
  useEffect(() => {
    function onKeyDown(e) {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return
      if (e.ctrlKey || e.metaKey || e.altKey) return
      const key = e.key.toLowerCase()
      if (key === '?')      { setShowShortcuts((v) => !v); return }
      if (key === 'escape') { setShowShortcuts(false); setSidebarOpen(false); return }
      if (key === 'l')      { toggleTheme(); return }
      if (key === 'm')      { toggleAlarmMute(); return }
      if (key === 'f11') {
        e.preventDefault()
        if (!document.fullscreenElement) document.documentElement.requestFullscreen?.()
        else document.exitFullscreen?.()
        return
      }
      if (KEY_NAV[key] && controller.session) setPage(KEY_NAV[key])
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [controller.session, toggleTheme, toggleAlarmMute])

  /* ── Render guards ───────────────────────────────────────────── */
  if (setupRequired === null) return <LoadingScreen />
  if (setupRequired) return <SetupPage onSetupComplete={() => setSetupRequired(false)} />

  if (!controller.session) {
    return (
      <LoginPanel
        onLogin={controller.login}
        error={controller.authError}
        isAuthenticating={controller.isAuthenticating}
        onSetup={() => setSetupRequired(true)}
      />
    )
  }

  const activeAlarmCount = controller.alarms?.active?.length ?? 0

  return (
    <div className="app-shell">
      {/* ── Sidebar overlay (tablet) ── */}
      <div
        className={`sidebar-overlay${sidebarOpen ? ' open' : ''}`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* ── Sidebar navigation ── */}
      <Navigation
        page={page}
        onNavigate={(p) => { setPage(p); setSidebarOpen(false) }}
        alarmCount={activeAlarmCount}
        session={controller.session}
        onLogout={controller.logout}
        controller={controller}
        isOpen={sidebarOpen}
      />

      {/* ── Main content area ── */}
      <div className="main-area">
        <TopBar
          title={PAGE_TITLES[page] || 'Motor Digital Twin'}
          connectionState={controller.connection?.state}
          clock={controller.clock}
          onShowShortcuts={() => setShowShortcuts(true)}
          onMenuToggle={() => setSidebarOpen((v) => !v)}
          healthState={healthState}
          rulHours={rulHours}
          alarmMuted={alarmMuted}
          onAlarmMuteToggle={toggleAlarmMute}
        />

        <main id="main-content" className="page-content" data-page={page} tabIndex="-1">
          {page === 'dashboard' && (
            <PageErrorBoundary pageName="dashboard">
              <DashboardPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'sensors' && (
            <PageErrorBoundary pageName="sensors">
              <SensorPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'diagnostics' && (
            <PageErrorBoundary pageName="diagnostics">
              <DiagnosticsPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'trends' && (
            <PageErrorBoundary pageName="trends">
              <TrendsPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'alarms' && (
            <PageErrorBoundary pageName="alarms">
              <AlarmsPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'reports' && (
            <PageErrorBoundary pageName="reports">
              <ReportPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'settings' && (
            <PageErrorBoundary pageName="settings">
              <SettingsPage controller={controller} />
            </PageErrorBoundary>
          )}
          {page === 'about' && (
            <PageErrorBoundary pageName="about">
              <AboutPage />
            </PageErrorBoundary>
          )}
        </main>
      </div>

      {/* ── Keyboard shortcuts overlay ── */}
      {showShortcuts && <KeyboardShortcuts onClose={() => setShowShortcuts(false)} />}
    </div>
  )
}

/* ── Root: providers wrap everything ─────────────────────────────── */
function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AppInner />
      </ToastProvider>
    </ThemeProvider>
  )
}

export default App
