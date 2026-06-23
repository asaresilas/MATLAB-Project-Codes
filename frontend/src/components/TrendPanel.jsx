function MiniSparkline({ points, color }) {
  const safePoints = points.length > 1 ? points : [0, 0]
  const max = Math.max(...safePoints)
  const min = Math.min(...safePoints)
  const range = max - min || 1
  const path = safePoints.map((point, index) => {
    const x = (index / (safePoints.length - 1 || 1)) * 100
    const y = 100 - ((point - min) / range) * 100
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')
  return <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="sparkline"><path d={path} fill="none" stroke={color} strokeWidth="3" vectorEffect="non-scaling-stroke" /></svg>
}

export function TrendPanel({ trendWindow, onTrendWindowChange, trendSeries }) {
  return (
    <section className="panel trend-panel">
      <div className="panel-header"><span>Trend Analytics</span><div className="window-switch">{['30s', '5m', '1h'].map((windowKey) => <button type="button" key={windowKey} className={`window-chip ${trendWindow === windowKey ? 'active' : ''}`} onClick={() => onTrendWindowChange(windowKey)}>{windowKey}</button>)}</div></div>
      <div className="trend-grid">{trendSeries.map((series) => <div key={series.key} className="trend-card"><div className="trend-title">{series.label}</div><div className="trend-value">{series.latest}</div><MiniSparkline points={series.points} color={series.color} /></div>)}</div>
    </section>
  )
}
