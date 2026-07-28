import { useEffect, useMemo, useRef, useState } from 'react'
import { appConfig } from '../config/appConfig.js'
import { authenticate } from '../services/authService.js'
import { createDashboardSocketClient } from '../services/wsClient.js'
import { createSimulationSample } from '../services/simulationEngine.js'
import { exportSessionAsCsv, exportSessionAsJson } from '../services/exportService.js'
import { sessionService, settingsService } from '../services/storage.js'
import { clampPercent, parseTimestamp } from '../utils/validation.js'

const createInitialModels = () => ([
  { name: 'CWRU', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
  { name: 'Induction', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
  { name: 'NASA/RUL', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
  { name: 'Current Signature', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
  { name: 'Thermal', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
  { name: 'Fusion', availability: 'loading', predictedClass: 'Pending', confidence: 0, uncertainty: 0, latencyMs: 0 },
])

const initialSeries = { current: [], vibration: [], temperature: [], predictionCertainty: [], health: [], rul: [], rpm: [], torque: [] }
const quantile = (values, percentile) => values.length === 0 ? 0 : [...values].sort((a, b) => a - b)[Math.min(values.length - 1, Math.floor((percentile / 100) * values.length))]
const formatRelativeTime = (value) => { if (!value) return 'Not received'; const seconds = Math.max(0, Math.round((Date.now() - value.getTime()) / 1000)); return seconds < 5 ? 'just now' : `${seconds}s ago` }
const defaultSettings = {
  machineLabel: appConfig.machineId,
  staleDataMs: appConfig.staleDataMs,
  currentImbalanceWarning: 8,
  currentImbalanceCritical: 12,
  temperatureWarning: 70,
  temperatureCritical: 85,
  exportFormat: 'json',
}

const clone = (value) => JSON.parse(JSON.stringify(value))

const deriveRecommendation = (healthState, connectionState) => {
  if (connectionState !== 'receiving_data' && connectionState !== 'simulation_mode') return 'Restore valid data before action'
  if (healthState === 'CRITICAL') return 'Schedule immediate inspection and shutdown review'
  if (healthState === 'WARNING') return 'Schedule maintenance assessment'
  return 'Continue normal operation'
}

const normalizeLivePayload = (payload, machineId, previousSensors, previousOperatingPoint) => {
  if (payload.type === 'dashboard_update') {
    return {
      timestamp: payload.timestamp,
      alert_level: payload.alert_level || payload.machine?.healthState || 'UNKNOWN',
      confidence: payload.confidence ?? 0,
      uncertainty: payload.uncertainty ?? 0,
      model_used: payload.model_used || 'UNAVAILABLE',
      inference_time_ms: payload.inference_time_ms ?? 0,
      fault_type_name: payload.fault_type_name || payload.machine?.faultTypeName || 'Healthy',
      explanation:     payload.explanation || '',
      machine: {
        machineId: payload.machine?.machineId || payload.machine_id || machineId,
        rulHours: payload.machine?.rulHours ?? null,
        faultTypeName: payload.fault_type_name || payload.machine?.faultTypeName || 'Healthy',
      },
      sensors:          payload.sensors || previousSensors,
      _sensorsFresh:    !!payload.sensors,
      operatingPoint: payload.operatingPoint || previousOperatingPoint,
      models: payload.models || {},
      diagnostics: payload.diagnostics || {},
      status: payload.status || 'success',
    }
  }

  return {
    timestamp: payload.timestamp,
    alert_level: payload.alert_level || 'UNKNOWN',
    fault_type_name: payload.fault_type_name || 'Healthy',
    explanation:     payload.explanation || '',
    confidence: payload.confidence ?? 0,
    uncertainty: payload.uncertainty ?? 0,
    model_used: payload.model_used || 'UNAVAILABLE',
    inference_time_ms: payload.inference_time_ms ?? 0,
    machine: {
      machineId: payload.machine_id || machineId,
      // Use real rul_hours from the backend when present (added in websocket_handler v2.2).
      // Fall back to class-based approximation ONLY when:
      //   (a) rul_hours is absent (old backend), AND
      //   (b) prediction is a probability in [0, 1] — NOT a class index (0/1/2).
      //   Class indices would give nonsensical results e.g. (1-2)*20000 = -20000 h.
      // null means "not yet received" — prevents TopBar showing a fabricated value.
      rulHours: payload.rul_hours != null
        ? Number(payload.rul_hours)
        : (payload.prediction != null && Number(payload.prediction) >= 0 && Number(payload.prediction) <= 1)
          ? (1 - Number(payload.prediction)) * 20000
          : null,
    },
    sensors: previousSensors,
    operatingPoint: previousOperatingPoint,
    models: {
      Fusion: {
        availability: payload.status || 'available',
        predictedClass: payload.alert_level || 'UNKNOWN',
        confidence: payload.confidence ?? 0,
        uncertainty: payload.uncertainty ?? 0,
        latencyMs: payload.inference_time_ms ?? 0,
      },
    },
    diagnostics: {
      backendState: payload.status === 'success' ? 'healthy' : payload.status || 'degraded',
      lastPredictionTimeMs: payload.inference_time_ms ?? 0,
    },
    status: payload.status || 'success',
  }
}

export function useDashboardController() {
  const [mode, setMode] = useState('LIVE')
  const [clock, setClock] = useState(new Date().toISOString())
  const [connectionState, setConnectionState] = useState('booting')
  const [backendState, setBackendState] = useState('unknown')
  const [modelRegistryState, setModelRegistryState] = useState('loading')
  const [session, setSession] = useState(() => sessionService.loadSession())
  const [authError, setAuthError] = useState('')
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [settings, setSettings] = useState(() => settingsService.loadSettings(defaultSettings))
  const [machine, setMachine] = useState({ machineId: appConfig.machineId, healthState: 'UNKNOWN', predictionCertainty: null, uncertainty: null, rulHours: null, modelUsed: 'Awaiting connection', lastPacketText: 'Not connected', lastInferenceText: 'Not connected' })
  const [operatingPoint, setOperatingPoint] = useState({ rpm: null, torque: null, ambient: null, load: 'Unknown' })
  const [sensors, setSensors] = useState({ phaseCurrent: { u: null, v: null, w: null, imbalance: null }, vibration: { rms: null, crestFactor: null, kurtosis: null, severity: 'Unknown' }, temperature: { stator: null, bearing: null, delta: null }, thermal: { state: 'Unavailable', hotSpot: null }, freshness: 'No data' })
  const [models, setModels] = useState(createInitialModels)
  const [trendWindow, setTrendWindow] = useState('30s')
  const [trendState, setTrendState] = useState(initialSeries)
  const [events, setEvents] = useState([])
  const [activeAlarms, setActiveAlarms] = useState([])
  const [diagnostics, setDiagnostics] = useState({ connectionState: 'booting', backendState: 'unknown', modelRegistryState: 'loading', invalidPacketCount: 0, droppedPacketCount: 0, stalePacketCount: 0, avgLatencyMs: 0, p95LatencyMs: 0, p99LatencyMs: 0, modelVersion: 'v1.0', appVersion: 'frontend-2.1', activeClients: 0 })
  const lastPacketRef = useRef(null)
  const inferenceTimesRef = useRef([])
  const eventIdRef = useRef(0)
  const simulationTickRef = useRef(0)
  const alarmRef = useRef(new Map())

  const pushEvent = (source, message) => {
    eventIdRef.current += 1
    const now = new Date()
    setEvents((prev) => [{ id: eventIdRef.current, source, message, time: now.toLocaleTimeString() }, ...prev].slice(0, 60))
  }

  const updateLatencyStats = (latencyMs) => {
    inferenceTimesRef.current = [...inferenceTimesRef.current, latencyMs].slice(-120)
    const avg = inferenceTimesRef.current.length === 0 ? 0 : inferenceTimesRef.current.reduce((sum, value) => sum + value, 0) / inferenceTimesRef.current.length
    setDiagnostics((prev) => ({
      ...prev,
      avgLatencyMs: Math.round(avg),
      p95LatencyMs: Math.round(quantile(inferenceTimesRef.current, 95)),
      p99LatencyMs: Math.round(quantile(inferenceTimesRef.current, 99)),
    }))
  }

  const syncAlarmSet = (derivedAlarms) => {
    const nextMap = new Map(alarmRef.current)
    const activeCodes = new Set()
    derivedAlarms.forEach((alarm) => {
      activeCodes.add(alarm.code)
      if (!nextMap.has(alarm.code)) {
        nextMap.set(alarm.code, { id: alarm.code, ...alarm, acknowledged: false, cleared: false })
        pushEvent(alarm.source, `Alarm raised: ${alarm.message}`)
      } else {
        const current = nextMap.get(alarm.code)
        nextMap.set(alarm.code, { ...current, ...alarm, cleared: false })
      }
    })
    Array.from(nextMap.keys()).forEach((code) => {
      if (!activeCodes.has(code)) {
        const current = nextMap.get(code)
        if (current && !current.cleared) nextMap.set(code, { ...current, cleared: true })
      }
    })
    alarmRef.current = nextMap
    setActiveAlarms(Array.from(nextMap.values()).filter((alarm) => !alarm.cleared))
  }

  const deriveAlarms = (sample, connection) => {
    const alarms = []
    if (connection === 'stale_data') alarms.push({ code: 'COM-002', severity: 'warning', source: 'Transport', message: 'Data stream is stale', raisedAt: new Date().toLocaleTimeString() })
    if (sample.healthState === 'CRITICAL') alarms.push({ code: 'AST-006', severity: 'critical', source: 'Fusion Engine', message: 'Health state escalated to critical', raisedAt: new Date().toLocaleTimeString() })
    if (sample.sensors.phaseCurrent.imbalance > settings.currentImbalanceWarning) alarms.push({ code: 'AST-002', severity: sample.sensors.phaseCurrent.imbalance > settings.currentImbalanceCritical ? 'critical' : 'warning', source: 'Current Signature', message: `Current imbalance ${sample.sensors.phaseCurrent.imbalance.toFixed(1)}%`, raisedAt: new Date().toLocaleTimeString() })
    if (sample.sensors.temperature.stator > settings.temperatureCritical) alarms.push({ code: 'AST-003', severity: 'critical', source: 'Thermal', message: `Stator temperature exceeded limit (${sample.sensors.temperature.stator.toFixed(1)} C)`, raisedAt: new Date().toLocaleTimeString() })
    // RUL alarm — only fires when a real RUL value has been received (not null/undefined).
    // Thresholds match TopBar pill colours: <50 h = critical, 50–100 h = warning.
    const rulVal = sample.machine?.rulHours
    if (rulVal != null && !isNaN(Number(rulVal)) && Number(rulVal) < 100) {
      const rulNum = Number(rulVal)
      alarms.push({ code: 'AST-005', severity: rulNum < 50 ? 'critical' : 'warning', source: 'NASA/RUL', message: `RUL below threshold — ${Math.round(rulNum)} h remaining`, raisedAt: new Date().toLocaleTimeString() })
    }
    return alarms
  }

  const appendTrendPoint = (key, value) => {
    const selectedWindow = appConfig.trendWindows.find((entry) => entry.key === trendWindow) || appConfig.trendWindows[0]
    setTrendState((prev) => ({ ...prev, [key]: [...prev[key], { t: Date.now(), v: Number(value) }].slice(-selectedWindow.maxPoints) }))
  }

  const applySample = (sample, sourceMode) => {
    const packetTime = parseTimestamp(sample.timestamp) || new Date()
    lastPacketRef.current = packetTime
    const healthState = sample.alert_level || 'UNKNOWN'
    const confidence = clampPercent((sample.confidence ?? 0) * 100)
    const uncertainty = clampPercent((sample.uncertainty ?? 0) * 100)
    const inferenceLatency = Math.round(Number(sample.inference_time_ms || 0))
    const runtimeState = sourceMode === 'LIVE' ? 'receiving_data' : 'simulation_mode'

    setConnectionState(runtimeState)
    setBackendState(sourceMode === 'LIVE' ? (sample.diagnostics?.backendState || 'healthy') : 'simulated')
    setModelRegistryState('available')
    setDiagnostics((prev) => ({
      ...prev,
      connectionState: runtimeState,
      backendState: sourceMode === 'LIVE' ? (sample.diagnostics?.backendState || 'healthy') : 'simulated',
      modelRegistryState: 'available',
      activeClients: sample.diagnostics?.activeClients ?? prev.activeClients,
    }))
    updateLatencyStats(inferenceLatency)

    const nextMachine = {
      machineId: sample.machine?.machineId || settings.machineLabel,
      healthState,
      faultTypeName: sample.fault_type_name || sample.machine?.faultTypeName || 'Healthy',
      explanation:   sample.explanation || '',
      predictionCertainty: confidence,
      uncertainty,
      rulHours: sample.machine?.rulHours != null ? Math.round(sample.machine.rulHours) : null,
      modelUsed: sample.model_used || 'Unavailable',
      lastPacketText: formatRelativeTime(packetTime),
      lastInferenceText: formatRelativeTime(packetTime),
    }
    setMachine(nextMachine)
    setOperatingPoint({
      rpm:     sample.operatingPoint?.rpm     ?? null,
      torque:  sample.operatingPoint?.torque  ?? null,
      ambient: sample.operatingPoint?.ambient ?? null,
      load:    sample.operatingPoint?.load    ?? 'Unknown',
    })
    const sensorFresh = sample._sensorsFresh !== false  // false only when explicitly stale
    setSensors({
      ...sample.sensors,
      freshness: sensorFresh
        ? `Updated ${formatRelativeTime(packetTime)}`
        : `⚠ Prior packet — ${formatRelativeTime(packetTime)}`,
      _stale: !sensorFresh,
    })

    const orderedModels = ['CWRU', 'Induction', 'NASA/RUL', 'Current Signature', 'Thermal', 'Fusion']
    const nextModels = orderedModels.map((name) => {
      const incoming = sample.models?.[name] || sample.models?.[name.replace('/RUL', '')] || sample.models?.[name.split(' ')[0]]
      return {
        name,
        availability: incoming?.availability || (name === 'Fusion' ? 'available' : 'standby'),
        predictedClass: incoming?.predictedClass || (name === 'Fusion' ? healthState : 'No inference'),
        confidence: clampPercent((incoming?.confidence ?? (name === 'Fusion' ? sample.confidence ?? 0 : 0)) * 100),
        uncertainty: clampPercent((incoming?.uncertainty ?? (name === 'Fusion' ? sample.uncertainty ?? 0 : 0)) * 100),
        latencyMs: Math.round(incoming?.latencyMs || (name === 'Fusion' ? inferenceLatency : 0)),
      }
    })
    setModels(nextModels)

    // Only append numeric values — skip null/NaN to avoid phantom zeros in charts.
    if (sample.sensors.phaseCurrent.u     != null) appendTrendPoint('current',             sample.sensors.phaseCurrent.u)
    if (sample.sensors.vibration.rms      != null) appendTrendPoint('vibration',           sample.sensors.vibration.rms)
    if (sample.sensors.temperature.stator != null) appendTrendPoint('temperature',         sample.sensors.temperature.stator)
    if (sample.operatingPoint?.rpm        != null) appendTrendPoint('rpm',                 sample.operatingPoint.rpm)
    if (sample.operatingPoint?.torque     != null) appendTrendPoint('torque',              sample.operatingPoint.torque)
    appendTrendPoint('predictionCertainty', confidence)
    appendTrendPoint('health', healthState === 'CRITICAL' ? 2 : healthState === 'WARNING' ? 1 : 0)
    if (sample.machine?.rulHours != null) appendTrendPoint('rul', sample.machine.rulHours)
    syncAlarmSet(deriveAlarms({ ...sample, healthState }, runtimeState))
  }

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date().toISOString()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    settingsService.saveSettings(settings)
  }, [settings])

  useEffect(() => {
    if (settings.machineLabel !== machine.machineId && machine.healthState === 'UNKNOWN') {
      setMachine((prev) => ({ ...prev, machineId: settings.machineLabel }))
    }
  }, [settings.machineLabel, machine.healthState, machine.machineId])

  useEffect(() => {
    const staleTimer = setInterval(() => {
      if (!lastPacketRef.current || mode !== 'LIVE' || !session) return
      const age = Date.now() - lastPacketRef.current.getTime()
      if (age > Number(settings.staleDataMs)) {
        setConnectionState('stale_data')
        setDiagnostics((prev) => ({ ...prev, connectionState: 'stale_data', stalePacketCount: prev.stalePacketCount + 1 }))
        syncAlarmSet(deriveAlarms({ healthState: machine.healthState, machine: { rulHours: machine.rulHours }, sensors }, 'stale_data'))
      }
    }, 1000)
    return () => clearInterval(staleTimer)
  }, [mode, session, settings.staleDataMs, machine.healthState, machine.rulHours, sensors])

  useEffect(() => {
    if (!session || mode !== 'LIVE') return undefined
    const client = createDashboardSocketClient({
      url: appConfig.wsUrl,
      reconnectBaseMs: appConfig.reconnectBaseMs,
      reconnectMaxMs: appConfig.reconnectMaxMs,
      onStateChange: (state) => {
        setConnectionState(state)
        setDiagnostics((prev) => ({ ...prev, connectionState: state }))
        if (state === 'connected') pushEvent('Transport', 'Connected to dashboard stream')
        if (state === 'disconnected') pushEvent('Transport', 'Disconnected from dashboard stream')
      },
      onMessage: (payload) => {
        if (payload.type === 'connection_confirmed') {
          pushEvent('Transport', payload.message || 'Handshake confirmed')
          setBackendState(payload.backend_state || 'healthy')
          setDiagnostics((prev) => ({ ...prev, backendState: payload.backend_state || 'healthy', activeClients: payload.active_clients ?? prev.activeClients }))
          return
        }
        // Backend heartbeat — acknowledge liveness but do NOT overwrite machine state.
        if (payload.type === 'ping') {
          setBackendState('healthy')
          return
        }
        // Ignore unknown non-data message types silently (ground_truth_ack, etc.)
        if (!['dashboard_update', 'prediction'].includes(payload.type)) return
        const normalized = normalizeLivePayload(payload, settings.machineLabel, clone(sensors), clone(operatingPoint))
        applySample(normalized, 'LIVE')
      },
      onError: (message) => {
        setBackendState('degraded')
        setDiagnostics((prev) => ({ ...prev, backendState: 'degraded', invalidPacketCount: prev.invalidPacketCount + 1 }))
        pushEvent('Transport', message)
      },
    })
    client.connect()
    return () => client.close()
  }, [session, mode, settings.machineLabel])

  useEffect(() => {
    if (!session || mode === 'LIVE') return undefined
    setConnectionState(mode === 'SIMULATION' ? 'simulation_mode' : mode === 'REPLAY' ? 'replay_mode' : 'offline_review')
    setBackendState(mode === 'SIMULATION' ? 'simulated' : 'offline')
    pushEvent('Mode', `Switched to ${mode}`)
    if (mode !== 'SIMULATION') return undefined
    const scenarioKey = machine.healthState === 'CRITICAL' ? 'critical' : machine.healthState === 'WARNING' ? 'drift' : 'healthy'
    const timer = setInterval(() => {
      simulationTickRef.current += 1
      applySample(createSimulationSample(scenarioKey, simulationTickRef.current), 'SIMULATION')
    }, 2000)
    return () => clearInterval(timer)
  }, [session, mode, machine.healthState])

  const login = async ({ username, password }) => {
    if (!username || !password) {
      setAuthError('Username and password are required.')
      return false
    }
    setIsAuthenticating(true)
    setAuthError('')
    try {
      const user = await authenticate(username, password)
      const nextSession = {
        username: user.username,
        role: user.role,
        displayName: user.displayName,
        token: user.token,
        loggedInAt: new Date().toISOString(),
      }
      sessionService.saveSession(nextSession)
      setSession(nextSession)
      pushEvent('Security', `${user.role} session started`)
      return true
    } catch (err) {
      setAuthError(err.message || 'Authentication failed.')
      return false
    } finally {
      setIsAuthenticating(false)
    }
  }

  const logout = () => {
    sessionService.clearSession()
    setSession(null)
    pushEvent('Security', 'Session closed')
  }

  const updateSettings = (patch) => {
    setSettings((prev) => ({ ...prev, ...patch }))
  }

  const exportReport = (format) => {
    const snapshot = {
      exportedAt: new Date().toISOString(),
      session,
      settings,
      machine,
      application: { mode, connectionState, backendState },
      diagnostics,
      alarms: { active: activeAlarms, events },
      operatingPoint,
      sensors,
      models,
      trends: trendState,
    }
    if (format === 'csv') exportSessionAsCsv(snapshot)
    else exportSessionAsJson(snapshot)
    pushEvent('Reporting', `Exported session report as ${format.toUpperCase()}`)
  }

  const acknowledgeAlarm = (alarmId) => {
    const current = alarmRef.current.get(alarmId)
    if (!current) return
    alarmRef.current.set(alarmId, { ...current, acknowledged: true })
    setActiveAlarms(Array.from(alarmRef.current.values()).filter((alarm) => !alarm.cleared))
    pushEvent('Operator', `Acknowledged alarm ${alarmId}`)
  }

  const acknowledgeAllWarnings = () => {
    Array.from(alarmRef.current.entries()).forEach(([id, alarm]) => {
      if (alarm.severity !== 'critical') alarmRef.current.set(id, { ...alarm, acknowledged: true })
    })
    setActiveAlarms(Array.from(alarmRef.current.values()).filter((alarm) => !alarm.cleared))
    pushEvent('Operator', 'Acknowledged all warning alarms')
  }

  const clearResolvedAlarms = () => {
    Array.from(alarmRef.current.entries()).forEach(([id, alarm]) => {
      if (alarm.cleared) alarmRef.current.delete(id)
    })
    setActiveAlarms(Array.from(alarmRef.current.values()).filter((alarm) => !alarm.cleared))
    pushEvent('Operator', 'Cleared resolved alarms')
  }

  const trendSeries = useMemo(() => {
    const lastV = (arr) => arr.length === 0 ? null : (typeof arr.at(-1) === 'object' ? arr.at(-1)?.v : arr.at(-1))
    const last  = (arr, dp, unit) => { const v = lastV(arr); return v == null ? '—' : `${v.toFixed(dp)}${unit ? ` ${unit}` : ''}` }
    const HEALTH_LABELS = ['NORMAL', 'WARNING', 'CRITICAL']
    return [
      { key: 'current',             label: 'Phase U Current',    latest: last(trendState.current,             2, 'A'),   points: trendState.current,             color: '#2563eb' },
      { key: 'vibration',           label: 'Vibration RMS',      latest: last(trendState.vibration,           2, 'g'),   points: trendState.vibration,           color: '#f97316' },
      { key: 'temperature',         label: 'Stator Temp',        latest: last(trendState.temperature,         1, '°C'),  points: trendState.temperature,         color: '#dc2626' },
      { key: 'rpm',                 label: 'Rotor Speed',        latest: last(trendState.rpm,                 0, 'RPM'), points: trendState.rpm,                 color: '#a78bfa' },
      { key: 'torque',              label: 'Shaft Torque',       latest: last(trendState.torque,              1, 'N·m'), points: trendState.torque,              color: '#38bdf8' },
      { key: 'predictionCertainty', label: 'Prediction Certainty', latest: last(trendState.predictionCertainty, 0, '%'), points: trendState.predictionCertainty, color: '#06b6d4' },
      { key: 'health',              label: 'Health State',       latest: trendState.health.length === 0 ? '—' : (HEALTH_LABELS[lastV(trendState.health)] ?? '—'), points: trendState.health, color: '#a855f7' },
      { key: 'rul',                 label: 'RUL',                latest: last(trendState.rul,                 0, 'h'),   points: trendState.rul,                 color: '#16a34a' },
    ]
  }, [trendState])

  return {
    session,
    authError,
    isAuthenticating,
    login,
    logout,
    mode,
    setMode,
    clock,
    machine,
    application: { mode, connectionState, dataState: connectionState === 'receiving_data' ? 'fresh' : connectionState, backendState },
    operatingPoint,
    sensors,
    signalQuality: { summary: connectionState === 'receiving_data' ? 'Validated live payloads' : mode === 'SIMULATION' ? 'Deterministic simulation scenario' : 'Awaiting valid data', signalQuality: connectionState === 'receiving_data' ? 'nominal' : 'degraded', packetState: connectionState },
    models,
    alarms: { active: activeAlarms, events },
    diagnostics,
    recommendation: deriveRecommendation(machine.healthState, connectionState),
    trendWindow,
    setTrendWindow,
    trendSeries,
    acknowledgeAlarm,
    acknowledgeAllWarnings,
    clearResolvedAlarms,
    connection: { state: connectionState },
    settings,
    updateSettings,
    exportReport,
  }
}
