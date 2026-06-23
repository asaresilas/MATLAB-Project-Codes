export function MetricCard({ label, value, unit, sub, status = 'accent' }) {
  const valClass = ['ok', 'warn', 'crit'].includes(status) ? status : ''

  return (
    <div className={`metric-card ${status}`}>
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${valClass}`}>
        {value ?? '—'}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  )
}
