export function clampPercent(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return 0
  return Math.max(0, Math.min(100, numeric))
}

export function parseTimestamp(value) {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value)

export function validateDashboardMessage(payload) {
  if (!isObject(payload)) {
    return { ok: false, error: 'Payload must be an object' }
  }

  if (payload.type === 'connection_confirmed') {
    return { ok: true }
  }

  if (payload.type === 'dashboard_update') {
    if (!payload.machine || !payload.sensors || !payload.diagnostics) {
      return { ok: false, error: 'Dashboard payload is missing machine, sensors, or diagnostics fields' }
    }
    return { ok: true }
  }

  if (payload.type === 'prediction') {
    if (!('alert_level' in payload) && !('prediction' in payload) && !('model_used' in payload)) {
      return { ok: false, error: 'Prediction payload is missing required fields' }
    }
    return { ok: true }
  }

  return { ok: true }
}
