/* IEC 60446 standard phase colours: L1=Brown→Red, L2=Black→Yellow, L3=Grey→Blue */
const PHASES = [
  { id: 'u', label: 'L1', sub: 'Phase U', color: '#ef4444', glow: 'rgba(239,68,68,0.18)' },
  { id: 'v', label: 'L2', sub: 'Phase V', color: '#f59e0b', glow: 'rgba(245,158,11,0.18)' },
  { id: 'w', label: 'L3', sub: 'Phase W', color: '#3b82f6', glow: 'rgba(59,130,246,0.18)' },
]

function PhasorDiagram({ u, v, w }) {
  /* Simple 3-phase phasor diagram — 120° apart, amplitude proportional to current */
  const avg = ((u ?? 0) + (v ?? 0) + (w ?? 0)) / 3 || 1
  const r = 36
  const cx = 52, cy = 52

  const phasors = [
    { angle: -90,      current: u ?? 0, color: '#ef4444' },
    { angle: -90+120,  current: v ?? 0, color: '#f59e0b' },
    { angle: -90+240,  current: w ?? 0, color: '#3b82f6' },
  ]

  return (
    <svg width="104" height="104" viewBox="0 0 104 104" aria-label="Phasor diagram">
      {/* Background circle */}
      <circle cx={cx} cy={cy} r={r+4} fill="var(--bg-raised)" stroke="var(--border)" strokeWidth="1" />
      {/* Reference circles */}
      <circle cx={cx} cy={cy} r={r}    fill="none" stroke="var(--border)" strokeWidth="0.6" />
      <circle cx={cx} cy={cy} r={r/2}  fill="none" stroke="var(--border)" strokeWidth="0.5" strokeDasharray="2 2" />
      {/* Centre cross */}
      <line x1={cx-r-4} y1={cy} x2={cx+r+4} y2={cy} stroke="var(--border-md)" strokeWidth="0.6" />
      <line x1={cx} y1={cy-r-4} x2={cx} y2={cy+r+4} stroke="var(--border-md)" strokeWidth="0.6" />
      {/* Phasor vectors */}
      {phasors.map(({ angle, current, color }) => {
        const mag = Math.min(r, r * (current / (avg * 1.5)))
        const rad = (angle * Math.PI) / 180
        const ex = cx + mag * Math.cos(rad)
        const ey = cy + mag * Math.sin(rad)
        return (
          <g key={angle}>
            <line x1={cx} y1={cy} x2={ex} y2={ey} stroke={color} strokeWidth="2.5" strokeLinecap="round" />
            <polygon
              points={`${ex},${ey} ${ex - 4 * Math.cos(rad - 0.5)},${ey - 4 * Math.sin(rad - 0.5)} ${ex - 4 * Math.cos(rad + 0.5)},${ey - 4 * Math.sin(rad + 0.5)}`}
              fill={color}
            />
          </g>
        )
      })}
      {/* Centre dot */}
      <circle cx={cx} cy={cy} r="3" fill="var(--txt-2)" />
    </svg>
  )
}

export function ThreePhaseCard({ u, v, w, imbalance, voltage = 400, frequency = 50 }) {
  const vals = { u: u ?? 0, v: v ?? 0, w: w ?? 0 }
  const maxCurrent = Math.max(vals.u, vals.v, vals.w, 0.01)
  const avg = (vals.u + vals.v + vals.w) / 3

  const imbalancePct = imbalance != null ? imbalance : 0
  const imbalanceStatus = imbalancePct > 15 ? 'crit' : imbalancePct > 8 ? 'warn' : 'ok'
  const imbalanceColor  = imbalancePct > 15 ? 'var(--crit)' : imbalancePct > 8 ? 'var(--warn)' : 'var(--ok)'
  const imbalanceLabel  = imbalancePct > 15 ? 'HIGH — CHECK SUPPLY' : imbalancePct > 8 ? 'ELEVATED' : 'BALANCED'

  return (
    <div className="card three-phase-card">
      {/* Header */}
      <div className="card-header">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="card-title">3-Phase Stator Current</span>
          <span style={{ fontSize: 11, color: 'var(--txt-3)', fontFamily: 'var(--mono)' }}>
            {voltage} V&nbsp;/&nbsp;{frequency} Hz&nbsp;/&nbsp;3&#981;
          </span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--txt-3)', fontFamily: 'var(--mono)' }}>
          I<sub>avg</sub>&nbsp;=&nbsp;<strong style={{ color: 'var(--txt)', fontSize: 13 }}>{avg.toFixed(2)}</strong>&nbsp;A
        </span>
      </div>

      <div className="card-body" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        {/* Phasor diagram */}
        <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <PhasorDiagram u={vals.u} v={vals.v} w={vals.w} />
          <span style={{ fontSize: 9.5, color: 'var(--txt-3)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Phasor</span>
        </div>

        {/* Phase columns */}
        <div style={{ flex: 1, display: 'flex', gap: 10 }}>
          {PHASES.map(({ id, label, sub, color, glow }) => {
            const val = vals[id]
            const pct = maxCurrent > 0 ? (val / maxCurrent) * 100 : 0
            return (
              <div key={id} className="phase-col" style={{ flex: 1, background: glow, border: `1px solid ${color}22`, borderRadius: 'var(--r)', padding: '10px 10px 8px' }}>
                {/* Phase label */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <span style={{ width: 9, height: 9, borderRadius: '50%', background: color, display: 'inline-block', boxShadow: `0 0 6px ${color}` }} />
                  <span style={{ fontWeight: 700, fontSize: 12.5, color }}>{label}</span>
                  <span style={{ fontSize: 10, color: 'var(--txt-3)', marginLeft: 'auto' }}>{sub}</span>
                </div>
                {/* Current value */}
                <div style={{ fontFamily: 'var(--mono)', fontSize: 22, fontWeight: 700, color: 'var(--txt)', lineHeight: 1, marginBottom: 8 }}>
                  {val.toFixed(2)}
                  <span style={{ fontSize: 12, color: 'var(--txt-3)', fontWeight: 400, marginLeft: 3 }}>A</span>
                </div>
                {/* Bar */}
                <div style={{ height: 6, background: 'var(--bg-raised)', borderRadius: 3, overflow: 'hidden', marginBottom: 4 }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.4s ease' }} />
                </div>
                {/* Percent of max */}
                <div style={{ fontSize: 10, color: 'var(--txt-3)', textAlign: 'right', fontFamily: 'var(--mono)' }}>
                  {pct.toFixed(0)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Imbalance footer */}
      <div style={{ borderTop: '1px solid var(--border)', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 11, color: 'var(--txt-3)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Phase Imbalance</span>
        <div style={{ flex: 1, height: 5, background: 'var(--bg-raised)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${Math.min(100, imbalancePct * 6.67)}%`, background: imbalanceColor, borderRadius: 3, transition: 'width 0.5s ease' }} />
        </div>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 700, color: imbalanceColor }}>
          {imbalancePct.toFixed(2)}%
        </span>
        <span style={{ fontSize: 10, fontWeight: 700, color: imbalanceColor, letterSpacing: '0.05em' }}>
          {imbalanceLabel}
        </span>
      </div>
    </div>
  )
}
