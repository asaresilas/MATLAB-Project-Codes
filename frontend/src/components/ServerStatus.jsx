/**
 * ServerStatus — sidebar panel showing live backend + MATLAB client connection.
 * Reads real connection state from the dashboard controller; no polling of its own.
 */

import { useEffect, useRef, useState } from 'react'
import { appConfig } from '../config/appConfig.js'

// dot colour helper
function dotClass(state) {
  if (state === 'ok' || state === 'healthy' || state === 'available' || state === 'receiving_data' || state === 'simulation_mode' || state === 'connected') return 'ok'
  if (state === 'warn' || state === 'degraded' || state === 'stale_data' || state === 'reconnecting') return 'warn'
  if (state === 'err' || state === 'error' || state === 'disconnected') return 'err'
  return 'idle'
}

function labelFor(state) {
  const map = {
    healthy:          'Healthy',
    available:        'Available',
    receiving_data:   'Receiving Data',
    simulation_mode:  'Simulation',
    connected:        'Connected',
    stale_data:       'Stale',
    reconnecting:     'Reconnecting…',
    degraded:         'Degraded',
    disconnected:     'Disconnected',
    error:            'Error',
    unknown:          'Unknown',
    loading:          'Loading…',
    booting:          'Booting…',
    simulated:        'Simulated',
    offline:          'Offline',
  }
  return map[state] || state || '—'
}

/**
 * Props:
 *  connectionState  – from controller.connection.state
 *  backendState     – from controller.application.backendState
 *  modelRegistryState – from controller.diagnostics.modelRegistryState
 *  diagnostics      – full diagnostics object
 *  mode             – LIVE | SIMULATION | REPLAY
 */
export function ServerStatus({ connectionState, backendState, modelRegistryState, diagnostics, mode }) {
  const [httpAlive, setHttpAlive] = useState(null)  // null = unknown, true, false
  const [matlabConnected, setMatlabConnected] = useState(null)
  const pollRef = useRef(null)

  // Poll the /health endpoint every 8 seconds to show real server reachability
  useEffect(() => {
    let cancelled = false

    async function check() {
      try {
        const res = await fetch(`${appConfig.apiBaseUrl}/health`, {
          signal: AbortSignal.timeout(3000),
          cache: 'no-store',
        })
        if (cancelled) return
        if (res.ok) {
          const data = await res.json().catch(() => ({}))
          setHttpAlive(true)
          // Backend may report active_clients count which tells us if MATLAB is connected
          const clients = data.active_clients ?? data.activeClients ?? diagnostics?.activeClients ?? 0
          setMatlabConnected(clients > 0)
        } else {
          setHttpAlive(false)
          setMatlabConnected(false)
        }
      } catch {
        if (!cancelled) {
          setHttpAlive(false)
          setMatlabConnected(false)
        }
      }
    }

    check()
    pollRef.current = setInterval(check, 8000)
    return () => { cancelled = true; clearInterval(pollRef.current) }
  }, [appConfig.apiBaseUrl, diagnostics?.activeClients])

  // Derive MATLAB / Simulink connection from ws state if HTTP poll doesn't give clients info
  const wsIsLive = connectionState === 'receiving_data'
  const matlabState = matlabConnected === true ? 'ok'
    : matlabConnected === false && httpAlive ? 'warn'
    : matlabConnected === null ? 'idle'
    : 'err'

  const httpState = httpAlive === true ? 'ok' : httpAlive === false ? 'err' : 'idle'

  const rows = [
    {
      label: 'API Server',
      state: httpState,
      value: httpAlive === true ? 'Running' : httpAlive === false ? 'Unreachable' : 'Checking…',
    },
    {
      label: 'WebSocket',
      state: dotClass(connectionState),
      value: labelFor(connectionState),
    },
    {
      label: 'Model Registry',
      state: dotClass(modelRegistryState),
      value: labelFor(modelRegistryState),
    },
    {
      label: 'MATLAB Client',
      state: wsIsLive ? 'ok' : matlabState,
      value: wsIsLive ? 'Data Flowing'
        : matlabConnected === true ? 'Connected'
        : matlabConnected === false ? 'Not Connected'
        : 'Unknown',
    },
    {
      label: 'Backend',
      state: dotClass(backendState),
      value: labelFor(backendState),
    },
    {
      label: 'Mode',
      state: mode === 'LIVE' ? 'ok' : mode === 'SIMULATION' ? 'warn' : 'idle',
      value: mode || '—',
    },
  ]

  return (
    <div className="server-status-panel">
      <div className="server-status-title">System Status</div>
      {rows.map(({ label, state, value }) => (
        <div className="server-status-row" key={label}>
          <span className={`server-status-dot ${state}`} />
          <span className="server-status-label">{label}</span>
          <span className="server-status-val">{value}</span>
        </div>
      ))}
      {diagnostics?.avgLatencyMs > 0 && (
        <div className="server-status-row" style={{ marginTop: 2 }}>
          <span className="server-status-dot ok" />
          <span className="server-status-label">Avg Latency</span>
          <span className="server-status-val">{diagnostics.avgLatencyMs} ms</span>
        </div>
      )}
    </div>
  )
}
