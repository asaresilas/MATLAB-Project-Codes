export function SensorCard({ name, value, unit, min = 0, max = 100, status = 'ok' }) {
  const numericValue = typeof value === 'number' ? value : parseFloat(value) || 0
  const pct = Math.min(100, Math.max(0, ((numericValue - min) / (max - min)) * 100))

  const barClass = status === 'ok' ? '' : status

  return (
    <div className="sensor-card">
      <div className="sensor-card-header">
        <span className="sensor-name">{name}</span>
        <span className={`sensor-status-dot ${status}`} />
      </div>

      <div className="sensor-reading">
        {value !== null && value !== undefined ? numericValue.toFixed(2) : '—'}
        <span className="unit">{unit}</span>
      </div>

      <div className="sensor-range">
        <div className="sensor-bar-track">
          <div className={`sensor-bar-fill ${barClass}`} style={{ width: `${pct}%` }} />
        </div>
        <div className="sensor-range-labels">
          <span>{min}{unit}</span>
          <span>{max}{unit}</span>
        </div>
      </div>
    </div>
  )
}
