export function MiniChart({ data = [], color = '#0ea5e9', height = 40 }) {
  if (!data || data.length < 2) {
    return <svg className="mini-chart" height={height}><text x="50%" y="55%" textAnchor="middle" fill="#64748b" fontSize="10">No data</text></svg>
  }

  const width = 200
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const pad = 4

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (width - pad * 2)
    const y = pad + (1 - (v - min) / range) * (height - pad * 2)
    return `${x},${y}`
  })

  const pathD = `M${points.join(' L')}`
  const areaD = `M${points[0]} L${points.join(' L')} L${points[points.length - 1].split(',')[0]},${height - pad} L${pad},${height - pad} Z`

  return (
    <svg className="mini-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" height={height}>
      <defs>
        <linearGradient id={`grad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.01" />
        </linearGradient>
      </defs>
      <path d={areaD} fill={`url(#grad-${color.replace('#','')})`} />
      <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
