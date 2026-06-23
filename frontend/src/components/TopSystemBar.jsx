import { StatusBadge } from './StatusBadge.jsx'

const toneMap = { connected: 'success', receiving_data: 'success', stale_data: 'warning', disconnected: 'neutral', connecting: 'info', backend_error: 'danger', models_loading: 'warning', degraded_mode: 'warning', simulation_mode: 'info', replay_mode: 'info', offline_review: 'neutral' }

export function TopSystemBar({ systemTitle, machineId, mode, onModeChange, connectionState, backendState, modelState, activeAlarmCount, clock, session, onLogout }) {
  return (
    <header className="top-system-bar panel">
      <div className="title-cluster">
        <div className="eyebrow">Operator HMI</div>
        <h1>{systemTitle}</h1>
        <div className="title-meta">Machine {machineId}</div>
      </div>
      <div className="mode-cluster">
        <label className="field-label" htmlFor="mode-select">Mode</label>
        <select id="mode-select" className="mode-select" value={mode} onChange={(event) => onModeChange(event.target.value)}>
          <option value="LIVE">LIVE</option>
          <option value="SIMULATION">SIMULATION</option>
          <option value="REPLAY">REPLAY</option>
          <option value="OFFLINE_REVIEW">OFFLINE REVIEW</option>
        </select>
      </div>
      <div className="top-status-grid">
        <div className="status-item"><div className="field-label">Connection</div><StatusBadge label={connectionState.replace('_', ' ')} tone={toneMap[connectionState] || 'neutral'} /></div>
        <div className="status-item"><div className="field-label">Backend</div><StatusBadge label={backendState} tone={backendState === 'healthy' ? 'success' : backendState === 'degraded' ? 'warning' : backendState === 'simulated' ? 'info' : 'neutral'} /></div>
        <div className="status-item"><div className="field-label">Models</div><StatusBadge label={modelState} tone={modelState === 'available' ? 'success' : modelState === 'loading' ? 'warning' : 'neutral'} /></div>
        <div className="status-item"><div className="field-label">Alarms</div><div className="metric-value">{activeAlarmCount}</div></div>
        <div className="status-item align-right"><div className="field-label">System Time</div><div className="mono-value">{clock}</div></div>
      </div>
      <div className="session-cluster">
        <div className="field-label">Signed in</div>
        <div className="session-name">{session.displayName}</div>
        <div className="session-role">{session.role}</div>
        <button type="button" className="secondary-button" onClick={onLogout}>Logout</button>
      </div>
    </header>
  )
}
