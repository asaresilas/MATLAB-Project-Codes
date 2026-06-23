/**
 * CategoricalTrend — Health state step-function chart
 *
 * Accepts points: { t: epochMs, v: 0|1|2 }[]
 *   v = 0 → NORMAL   (green)
 *   v = 1 → WARNING  (amber)
 *   v = 2 → CRITICAL (red)
 *
 * Renders:
 *   • Three horizontal colour bands (NORMAL/WARNING/CRITICAL)
 *   • Step-function line tracing health state transitions over time
 *   • Y-axis with categorical tick labels
 *   • X-axis with elapsed-time labels in seconds
 */

const LEVELS = [
  { v: 0, label: 'NORMAL',   color: '#22c55e', band: 'rgba(34,197,94,0.10)'   },
  { v: 1, label: 'WARNING',  color: '#f59e0b', band: 'rgba(245,158,11,0.10)'  },
  { v: 2, label: 'CRITICAL', color: '#ef4444', band: 'rgba(239,68,68,0.10)'   },
]

const toV = (p) => (p != null && typeof p === 'object' ? p.v : p)
const toT = (p) => (p != null && typeof p === 'object' ? p.t : null)

export function CategoricalTrend({ data = [], height = 300 }) {
  const W = 900
  const H = height
  const PAD = { top: 28, right: 36, bottom: 58, left: 90 }
  const cW = W - PAD.left - PAD.right
  const cH = H - PAD.top  - PAD.bottom

  /* ── Empty state ── */
  if (!data || data.length < 2) {
    return (
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: 'block' }}
        role="img" aria-label="Health state: collecting data">
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle"
          fill="var(--txt-3,#64748b)" fontSize="14" fontFamily="Inter,sans-serif">
          Collecting data — connect MATLAB/Simulink to begin health trend
        </text>
      </svg>
    )
  }

  /* Domain: 0–2 with padding so bands don't clip */
  const domMin = -0.4
  const domMax =  2.4
  const scX = (i) => PAD.left + (i / (data.length - 1)) * cW
  const scY = (v) => PAD.top + (1 - (v - domMin) / (domMax - domMin)) * cH

  /* Band boundaries (mid-points between levels) */
  const bandBounds = [
    { lvl: 0, yTop: scY(0.5),  yBot: scY(domMin) }, // NORMAL band: bottom
    { lvl: 1, yTop: scY(1.5),  yBot: scY(0.5)    }, // WARNING band: middle
    { lvl: 2, yTop: scY(domMax), yBot: scY(1.5)  }, // CRITICAL band: top
  ]

  /* Step-function path: horizontal then vertical step */
  const vals = data.map(toV)
  let stepPath = `M${scX(0).toFixed(1)},${scY(vals[0]).toFixed(1)}`
  for (let i = 1; i < vals.length; i++) {
    const x = scX(i).toFixed(1)
    const y = scY(vals[i]).toFixed(1)
    const yPrev = scY(vals[i - 1]).toFixed(1)
    stepPath += ` H${x} V${y}`
  }

  /* Current state color */
  const lastV   = vals[vals.length - 1]
  const curLevel = LEVELS[Math.round(Math.max(0, Math.min(2, lastV)))] ?? LEVELS[0]

  /* X-axis ticks */
  const N_XTICK = 7
  const lastTs  = toT(data[data.length - 1])
  const xTicks  = Array.from({ length: N_XTICK }, (_, i) => {
    const idx = Math.round((i / (N_XTICK - 1)) * (data.length - 1))
    const ts  = toT(data[idx])
    let lbl
    if (idx === data.length - 1) {
      lbl = '0 s'
    } else if (lastTs && ts) {
      lbl = `−${Math.round((lastTs - ts) / 1000)} s`
    } else {
      lbl = `−${(data.length - 1 - idx) * 2} s`
    }
    return { idx, x: scX(idx), lbl }
  })

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ display: 'block', overflow: 'visible' }}
      role="img"
      aria-label={`Health state trend. Current: ${curLevel.label}`}
    >
      {/* ── Background ── */}
      <rect x={PAD.left} y={PAD.top} width={cW} height={cH}
        fill="var(--bg-raised,#1e2535)" opacity="0.35" rx="2" />

      {/* ── Colour bands ── */}
      {bandBounds.map(({ lvl, yTop, yBot }) => {
        const level = LEVELS[lvl]
        return (
          <rect key={lvl}
            x={PAD.left} y={yTop}
            width={cW} height={yBot - yTop}
            fill={level.band}
          />
        )
      })}

      {/* Band separator lines */}
      <line x1={PAD.left} y1={scY(0.5)} x2={PAD.left + cW} y2={scY(0.5)}
        stroke="rgba(255,255,255,0.08)" strokeWidth="1" strokeDasharray="4 4" />
      <line x1={PAD.left} y1={scY(1.5)} x2={PAD.left + cW} y2={scY(1.5)}
        stroke="rgba(255,255,255,0.08)" strokeWidth="1" strokeDasharray="4 4" />

      {/* Band labels at left edge */}
      {LEVELS.map(({ v, label, color }) => (
        <text key={v}
          x={PAD.left + 8} y={scY(v)}
          dominantBaseline="middle"
          fill={color} fontSize="9" fontFamily="Inter,sans-serif" fontWeight="700"
          opacity="0.8">
          {label}
        </text>
      ))}

      {/* ── Axes ── */}
      <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + cH}
        stroke="var(--border-md,#3d4f6e)" strokeWidth="1.4" />
      <line x1={PAD.left} y1={PAD.top + cH} x2={PAD.left + cW} y2={PAD.top + cH}
        stroke="var(--border-md,#3d4f6e)" strokeWidth="1.4" />

      {/* ── Y-axis categorical tick marks ── */}
      {LEVELS.map(({ v, label, color }) => {
        const y = scY(v)
        return (
          <g key={v}>
            <line x1={PAD.left - 5} y1={y} x2={PAD.left} y2={y}
              stroke="var(--border-md,#3d4f6e)" strokeWidth="1.2" />
            <text x={PAD.left - 9} y={y}
              textAnchor="end" dominantBaseline="middle"
              fill={color} fontSize="10" fontFamily="Inter,sans-serif" fontWeight="600">
              {label}
            </text>
          </g>
        )
      })}

      {/* Y-axis title */}
      <text
        x={14} y={PAD.top + cH / 2}
        textAnchor="middle" dominantBaseline="middle"
        fill="var(--txt-2,#94a3b8)" fontSize="11" fontFamily="Inter,sans-serif" fontWeight="600"
        transform={`rotate(-90, 14, ${PAD.top + cH / 2})`}
      >
        Health State
      </text>

      {/* ── X-axis ticks ── */}
      {xTicks.map(({ idx, x, lbl }) => (
        <g key={idx}>
          <line x1={x} y1={PAD.top + cH} x2={x} y2={PAD.top + cH + 5}
            stroke="var(--border-md,#3d4f6e)" strokeWidth="1" />
          <text x={x} y={PAD.top + cH + 17}
            textAnchor="middle"
            fill="var(--txt-3,#64748b)" fontSize="9.5" fontFamily="JetBrains Mono,monospace">
            {lbl}
          </text>
        </g>
      ))}

      {/* X-axis title */}
      <text
        x={PAD.left + cW / 2} y={H - 6}
        textAnchor="middle"
        fill="var(--txt-3,#64748b)" fontSize="10.5" fontFamily="Inter,sans-serif"
      >
        Elapsed Time — most recent at right (ISO 13373-3)
      </text>

      {/* ── Step-function health line ── */}
      <path d={stepPath} fill="none" stroke={curLevel.color}
        strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter"
        opacity="0.95"
      />

      {/* ── Live endpoint dot ── */}
      <circle cx={scX(data.length - 1)} cy={scY(lastV)}
        r="5"
        fill={curLevel.color}
        stroke="var(--bg-surface,#161b25)"
        strokeWidth="2.5"
      />
      <text x={scX(data.length - 1) + 8} y={scY(lastV)}
        dominantBaseline="middle"
        fill={curLevel.color} fontSize="10.5" fontFamily="Inter,sans-serif" fontWeight="700">
        {curLevel.label}
      </text>
    </svg>
  )
}
