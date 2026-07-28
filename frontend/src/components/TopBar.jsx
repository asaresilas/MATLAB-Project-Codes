import { useEffect, useState } from 'react'
import { useTheme } from '../context/ThemeContext.jsx'

/* ── Connection state config ──────────────────────────────────────── */
const STATE_CONFIG = {
  receiving_data:  { cls: 'ok',   label: '● Live',          title: 'Data flowing from MATLAB/Simulink' },
  simulation_mode: { cls: 'ok',   label: '◎ Simulation',    title: 'Running in simulation mode' },
  connected:       { cls: 'ok',   label: '● Connected',     title: 'WebSocket connected' },
  stale_data:      { cls: 'warn', label: '◑ Stale Data',    title: 'No new data for > 5 s' },
  connecting:      { cls: 'warn', label: '↺ Connecting',    title: 'Establishing WebSocket connection…' },
  reconnecting:    { cls: 'warn', label: '↺ Reconnecting',  title: 'Attempting to reconnect…' },
  degraded:        { cls: 'warn', label: '◑ Degraded',      title: 'Partial data available' },
  disconnected:    { cls: 'err',  label: '○ Disconnected',  title: 'WebSocket closed' },
  error:           { cls: 'err',  label: '✕ Error',         title: 'Connection error' },
  booting:         { cls: 'idle', label: '⋯ Booting',       title: 'System initialising…' },
}

/* ── TopBar ───────────────────────────────────────────────────────── */
export function TopBar({ title, connectionState, clock, onShowShortcuts, healthState, rulHours, onMenuToggle, alarmMuted, onAlarmMuteToggle }) {
  const { theme, toggle } = useTheme()
  const [isFs, setIsFs]   = useState(false)

  /* Track fullscreen state */
  useEffect(() => {
    const handler = () => setIsFs(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', handler)
    return () => document.removeEventListener('fullscreenchange', handler)
  }, [])

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.()
    } else {
      document.exitFullscreen?.()
    }
  }

  /* Pill */
  const { cls: pillCls, label: pillLabel, title: pillTitle } =
    STATE_CONFIG[connectionState] ?? { cls: 'idle', label: '○ Offline', title: 'Not connected' }

  /* Clock — guard against invalid timestamps */
  const clockDate = clock ? new Date(clock) : null
  const clockOk   = clockDate && !isNaN(clockDate.getTime())
  const timeStr   = clockOk
    ? clockDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
    : '--:--:--'
  const dateStr   = clockOk
    ? clockDate.toLocaleDateString([], { weekday: 'short', year: 'numeric', month: 'short', day: '2-digit' })
    : '---'

  /* Health */
  const healthKey = (healthState || 'unknown').toUpperCase()
  const healthCls = { NORMAL: 'ok', WARNING: 'warn', CRITICAL: 'err' }[healthKey] || 'idle'
  const healthLabel = healthKey === 'UNKNOWN' ? '— Unknown' : healthKey

  /* RUL display */
  const rulNum  = parseFloat(rulHours)
  const rulStr  = isNaN(rulNum) ? '—' : rulNum.toFixed(0)
  const rulCls  = isNaN(rulNum) ? 'idle' : rulNum < 50 ? 'err' : rulNum < 150 ? 'warn' : 'ok'

  return (
    <header className="topbar">
      {/* ── Skip link (accessibility) ── */}
      <a href="#main-content" className="skip-link">Skip to main content</a>

      {/* ── Hamburger (tablet/mobile) ── */}
      <button className="hamburger-btn" onClick={onMenuToggle} aria-label="Toggle navigation menu">
        <HamburgerIcon />
      </button>

      {/* ── Left: page title ── */}
      <span className="topbar-title">{title}</span>

      {/* ── Centre: health + RUL + connection + clock ── */}
      <div className="topbar-status-group">
        {/* Global machine health */}
        <div className={`health-pill ${healthCls}`} aria-live="polite" role="status" title="Overall machine health state">
          <ShapeIcon state={healthCls} />
          {healthLabel}
        </div>

        {/* RUL countdown */}
        <div className={`rul-pill ${rulCls}`} title="Remaining Useful Life">
          <span className="rul-pill-label">RUL</span>
          <span className="rul-pill-value">{rulStr}</span>
          <span className="rul-pill-unit">h</span>
        </div>

        <div className="topbar-divider" />
      </div>

      {/* ── Right of divider: connection + clock ── */}
      <div className="topbar-status-group">
        <div className={`conn-pill ${pillCls}`} title={pillTitle}>
          <span className="conn-dot" />
          {pillLabel}
        </div>

        <div className="topbar-divider" />

        <div className="topbar-clock">
          {dateStr}&nbsp;&nbsp;{timeStr}
        </div>
      </div>

      {/* ── Right: action buttons ── */}
      <div className="topbar-right">
        {/* Keyboard shortcuts */}
        <button
          className="topbar-icon-btn"
          onClick={onShowShortcuts}
          title="Keyboard shortcuts  (?)"
          aria-label="Show keyboard shortcuts"
        >
          <KeyboardIcon />
        </button>

        {/* Fullscreen */}
        <button
          className="topbar-icon-btn"
          onClick={toggleFullscreen}
          title={isFs ? 'Exit fullscreen  (F11)' : 'Enter fullscreen  (F11)'}
          aria-label="Toggle fullscreen"
        >
          {isFs ? <ExitFsIcon /> : <EnterFsIcon />}
        </button>

        {/* Alarm mute (shown only when muted) */}
        {alarmMuted !== undefined && (
          <button
            className={`topbar-icon-btn${alarmMuted ? ' alarm-muted-btn' : ''}`}
            onClick={onAlarmMuteToggle}
            title={alarmMuted ? 'Alarm sound muted — click to unmute' : 'Mute alarm sounds'}
            aria-label={alarmMuted ? 'Unmute alarm sounds' : 'Mute alarm sounds'}
            aria-pressed={alarmMuted}
          >
            {alarmMuted ? <MuteIcon /> : <SpeakerIcon />}
          </button>
        )}

        {/* Theme toggle — cycles dark → light → high-contrast */}
        <button
          className="theme-toggle topbar-icon-btn"
          onClick={toggle}
          title={
            theme === 'dark'           ? 'Switch to light mode'          :
            theme === 'light'          ? 'Switch to high-contrast mode'  :
                                         'Switch to dark mode'
          }
          aria-label="Cycle colour theme"
        >
          {theme === 'dark'  ? <SunIcon />      :
           theme === 'light' ? <MoonIcon />     :
                               <ContrastIcon />}
        </button>
      </div>
    </header>
  )
}

/* ── Colour-blind safe shape icon ────────────────────────────────── */
function ShapeIcon({ state }) {
  if (state === 'ok')   return <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="4.5" fill="currentColor" /></svg>
  if (state === 'warn') return <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><polygon points="5,0.5 9.5,9.5 0.5,9.5" fill="currentColor" /></svg>
  if (state === 'err')  return <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><polygon points="5,0.5 9.5,5 5,9.5 0.5,5" fill="currentColor" /></svg>
  return <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><rect x="1" y="1" width="8" height="8" rx="2" fill="currentColor" opacity="0.6" /></svg>
}

/* ── SVG icons ────────────────────────────────────────────────────── */

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1"  x2="12" y2="3"  />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22"  x2="5.64" y2="5.64"  />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1"  y1="12" x2="3"  y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}

function KeyboardIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <line x1="6"  y1="10" x2="6"  y2="10" strokeWidth="3" strokeLinecap="round" />
      <line x1="10" y1="10" x2="10" y2="10" strokeWidth="3" strokeLinecap="round" />
      <line x1="14" y1="10" x2="14" y2="10" strokeWidth="3" strokeLinecap="round" />
      <line x1="18" y1="10" x2="18" y2="10" strokeWidth="3" strokeLinecap="round" />
      <line x1="8"  y1="14" x2="16" y2="14" strokeWidth="2" strokeLinecap="round" />
      <line x1="6"  y1="14" x2="6"  y2="14" strokeWidth="3" strokeLinecap="round" />
      <line x1="18" y1="14" x2="18" y2="14" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

function EnterFsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3"  x2="14" y2="10" />
      <line x1="3"  y1="21" x2="10" y2="14" />
    </svg>
  )
}

function HamburgerIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6"  x2="21" y2="6"  />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
}

function ExitFsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="8 3 8 8 3 8" />
      <polyline points="21 8 16 8 16 3" />
      <polyline points="3 16 8 16 8 21" />
      <polyline points="16 21 16 16 21 16" />
    </svg>
  )
}

function ContrastIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3v18" />
      <path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none" />
    </svg>
  )
}

function SpeakerIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  )
}

function MuteIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <line x1="23" y1="9" x2="17" y2="15" />
      <line x1="17" y1="9" x2="23" y2="15" />
    </svg>
  )
}
