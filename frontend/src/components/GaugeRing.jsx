export function GaugeRing({ value = 0, max = 100, unit = '', label = '', status = 'ok', size = 110 }) {
  const R = (size - 20) / 2
  const circumference = 2 * Math.PI * R
  const pct = Math.min(1, Math.max(0, value / max))
  const offset = circumference * (1 - pct * 0.75)
  const strokeColor = { ok: '#22c55e', warn: '#f59e0b', crit: '#ef4444' }[status] || '#0ea5e9'

  return (
    <div className="gauge-wrap">
      <div className="gauge-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            className="gauge-track"
            cx={size / 2}
            cy={size / 2}
            r={R}
            strokeWidth="8"
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            strokeDashoffset={circumference * 0.125}
          />
          <circle
            className="gauge-fill"
            cx={size / 2}
            cy={size / 2}
            r={R}
            strokeWidth="8"
            stroke={strokeColor}
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            strokeDashoffset={offset + circumference * 0.125}
          />
        </svg>
        <div
          className="gauge-center"
          aria-live="polite"
          aria-atomic="true"
          aria-label={`${label}: ${typeof value === 'number' ? value.toFixed(1) : '—'} ${unit}`}
        >
          <span className="gauge-value" aria-hidden="true">{typeof value === 'number' ? value.toFixed(1) : '—'}</span>
          <span className="gauge-unit"  aria-hidden="true">{unit}</span>
        </div>
      </div>
      {label && <div className="gauge-label">{label}</div>}
    </div>
  )
}
