import { useState } from 'react'
import { ServerStatus } from './ServerStatus.jsx'

/* ── NavBtn must live OUTSIDE Navigation so React doesn't create a new
   component type on every render (which would cause full remounts).    */
function NavBtn({ id, label, icon: Icon, badge, activePage, onNavigate }) {
  const isActive = activePage === id
  return (
    <button
      className={`nav-item${isActive ? ' active' : ''}`}
      onClick={() => onNavigate(id)}
      aria-current={isActive ? 'page' : undefined}
      title={label}
    >
      <Icon className="nav-item-icon" />
      {label}
      {id === 'alarms' && badge > 0  && <span className="nav-badge">{badge > 99 ? '99+' : badge}</span>}
      {id === 'alarms' && !badge     && <span className="nav-badge-zero" aria-hidden="true" title="No active alarms">✓</span>}
    </button>
  )
}

export function Navigation({ page, onNavigate, alarmCount, session, onLogout, controller, isOpen }) {
  const [statusOpen, setStatusOpen] = useState(false)   // collapsed by default
  const initials = (session?.displayName || session?.username || 'U')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  /* Nav items split into logical groups — ISA-101 sidebar grouping */
  const monitorItems = [
    { id: 'dashboard', label: 'Dashboard',    icon: DashIcon    },
    { id: 'sensors',   label: 'Live Sensors', icon: SensorIcon  },
    { id: 'trends',    label: 'Trends',       icon: TrendIcon   },
    { id: 'alarms',    label: 'Alarms',       icon: AlarmIcon,  badge: alarmCount },
    { id: 'reports',   label: 'Reports',      icon: ReportIcon  },
  ]
  const configItems = [
    { id: 'settings',  label: 'Settings',     icon: SettingsIcon },
    { id: 'about',     label: 'Help / About', icon: HelpIcon    },
  ]

  const machineId = controller?.machine?.machineId || 'SCIM-01'

  return (
    <nav className={`sidebar${isOpen ? ' open' : ''}`} aria-label="Main navigation">
      {/* ── Logo ── */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <MotorLogo />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">MotorGuard</span>
          <span className="sidebar-logo-sub">Digital Twin</span>
        </div>
      </div>

      {/* ── Machine ID ── */}
      <div className="sidebar-machine">
        <div className="sidebar-machine-label">Machine</div>
        <div className="sidebar-machine-id">{machineId}</div>
      </div>

      {/* ── Single scrolling nav section with logical divider ── */}
      <div className="nav-section">
        <div className="nav-section-label">Monitor</div>
        {monitorItems.map((item) => (
          <NavBtn key={item.id} {...item} activePage={page} onNavigate={onNavigate} />
        ))}

        <div className="nav-divider" />
        <div className="nav-section-label">System</div>
        {configItems.map((item) => (
          <NavBtn key={item.id} {...item} activePage={page} onNavigate={onNavigate} />
        ))}
      </div>

      {/* ── System Status (collapsible) ── */}
      <div className="sys-status-section">
        <button
          className="sys-status-toggle"
          onClick={() => setStatusOpen((v) => !v)}
          aria-expanded={statusOpen}
          aria-controls="sys-status-panel"
          title={statusOpen ? 'Collapse system status' : 'Expand system status'}
        >
          <span className="sys-status-toggle-label">
            <SystemStatusIcon />
            SYSTEM STATUS
          </span>
          <ChevronIcon open={statusOpen} />
        </button>

        {statusOpen && (
          <div id="sys-status-panel" role="region" aria-label="System status">
            <ServerStatus
              connectionState={controller?.connection?.state}
              backendState={controller?.application?.backendState}
              modelRegistryState={controller?.diagnostics?.modelRegistryState}
              diagnostics={controller?.diagnostics}
              mode={controller?.mode}
            />
          </div>
        )}
      </div>

      {/* ── User footer ── */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-username">{session?.displayName || session?.username || '—'}</div>
            <div className="sidebar-role">{session?.role || 'operator'}</div>
          </div>
          <button className="sidebar-logout" onClick={onLogout} title="Sign out">
            <LogoutIcon />
          </button>
        </div>
      </div>
    </nav>
  )
}

/* ── Inline SVG icons ─────────────────────────────────────────── */

function MotorLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v4M12 18v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M2 12h4M18 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
    </svg>
  )
}

function DashIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

function SensorIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12h3M19 12h3M12 2v3M12 19v3" />
      <circle cx="12" cy="12" r="4" />
      <path d="M5.64 5.64l2.12 2.12M16.24 16.24l2.12 2.12M16.24 7.76l2.12-2.12M5.64 18.36l2.12-2.12" />
    </svg>
  )
}

function TrendIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  )
}

function AlarmIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  )
}

function SettingsIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}

function LogoutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}

function ReportIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
}

function HelpIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}

function SystemStatusIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  )
}

function ChevronIcon({ open }) {
  return (
    <svg
      width="12" height="12" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease', flexShrink: 0 }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}
