/**
 * TrendChart — Professional engineering trend chart
 *
 * Accepts data as:
 *   • { t: epochMs, v: number }[]   (timestamped — preferred)
 *   • number[]                       (legacy / backward compat)
 *
 * Features:
 *  • Rotated Y-axis title with unit
 *  • X-axis with elapsed-time labels in seconds ("0 s", "−4 s"…)
 *  • Hover tooltip: absolute HH:MM:SS, value+unit, threshold distance
 *  • 6 Y-axis ticks with numeric labels
 *  • Light horizontal grid lines
 *  • Amber / red dashed threshold lines with inline labels
 *  • Min ▼ / Max ▲ annotated markers
 *  • Live-endpoint dot
 *  • mini mode: area-only sparkline (no axes)
 */
import { useState } from 'react'

/* Extract plain numeric value from either format */
const toV = (p) => (p != null && typeof p === 'object' ? p.v : p)
const toT = (p) => (p != null && typeof p === 'object' ? p.t : null)

export function TrendChart({
  data    = [],
  color   = '#0ea5e9',
  unit    = '',
  label   = '',
  height  = 300,
  warnAt  = null,
  critAt  = null,
  mini    = false,
}) {
  const [tooltip, setTooltip] = useState(null)

  const W = 900
  const H = height

  /* Paddings — larger left/bottom to fit bigger axis labels */
  const PAD = mini
    ? { top: 4,  right: 4,  bottom: 4,  left: 4  }
    : { top: 32, right: 48, bottom: 76, left: 96 }

  const cW = W - PAD.left - PAD.right
  const cH = H - PAD.top  - PAD.bottom

  /* Extract numeric values */
  const vals = data.map(toV)

  /* ── Empty state ── */
  if (!data || data.length < 2) {
    return (
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: 'block' }}
        role="img" aria-label={`${label}: collecting data`}>
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle"
          fill="var(--txt-3,#64748b)" fontSize="14" fontFamily="Inter,sans-serif">
          Collecting data — connect MATLAB/Simulink to begin trend logging
        </text>
      </svg>
    )
  }

  /* ── Domain ── */
  const rawMin = Math.min(...vals)
  const rawMax = Math.max(...vals)
  const range  = rawMax - rawMin || Math.abs(rawMax) * 0.2 || 1
  const pad    = range * 0.15
  const domMin = rawMin - pad
  const domMax = rawMax + pad

  /* ── Scales ── */
  const scX = (i) => PAD.left + (i / (data.length - 1)) * cW
  const scY = (v) => PAD.top  + (1 - (v - domMin) / (domMax - domMin)) * cH

  /* ── Paths ── */
  const pts      = vals.map((v, i) => `${scX(i).toFixed(1)},${scY(v).toFixed(1)}`)
  const linePath = `M${pts.join(' L')}`
  const areaPath = [
    `M${scX(0).toFixed(1)},${(PAD.top + cH).toFixed(1)}`,
    `L${pts.join(' L')}`,
    `L${scX(data.length - 1).toFixed(1)},${(PAD.top + cH).toFixed(1)} Z`,
  ].join(' ')

  /* ── Y-axis ticks (6 equally-spaced) ── */
  const N_YTICK = 6
  const yTicks = Array.from({ length: N_YTICK }, (_, i) => {
    const frac = i / (N_YTICK - 1)
    const v    = domMin + frac * (domMax - domMin)
    return { v, y: scY(v) }
  })

  /* Y-axis tick formatter */
  const fmtY = (v) => {
    const abs = Math.abs(v)
    if (abs >= 1000) return `${(v / 1000).toFixed(1)}k`
    if (abs >= 100)  return v.toFixed(0)
    if (abs >= 10)   return v.toFixed(1)
    return v.toFixed(2)
  }

  /* ── X-axis ticks (7 evenly-spaced) with elapsed-time labels ── */
  const N_XTICK = 7
  const lastTs  = toT(data[data.length - 1])
  const xTicks  = mini ? [] : Array.from({ length: N_XTICK }, (_, i) => {
    const idx = Math.round((i / (N_XTICK - 1)) * (data.length - 1))
    const ts  = toT(data[idx])
    let lbl
    if (idx === data.length - 1) {
      lbl = '0 s'
    } else if (lastTs && ts) {
      const elapsed = Math.round((lastTs - ts) / 1000)
      lbl = `−${elapsed} s`
    } else {
      lbl = `−${(data.length - 1 - idx) * 2} s`
    }
    return { idx, x: scX(idx), lbl }
  })

  /* ── Min / Max indices ── */
  const maxIdx = vals.indexOf(rawMax)
  const minIdx = vals.indexOf(rawMin)

  /* ── Gradient & clip IDs ── */
  const gradId = `grad-${color.replace(/[^a-z0-9]/gi, '')}-${cH}`
  const clipId = `clip-${gradId}`

  /* ── Threshold line helper ── */
  const threshLine = (value, clr) => {
    if (value == null || value < domMin || value > domMax) return null
    const y = scY(value)
    return (
      <g key={`t${value}`}>
        <line x1={PAD.left} y1={y} x2={PAD.left + cW} y2={y}
          stroke={clr} strokeWidth="1.4" strokeDasharray="6 4" opacity="0.9" />
        <text x={PAD.left + cW - 4} y={y - 7}
          textAnchor="end" fill={clr} fontSize="14" fontFamily="JetBrains Mono,monospace"
          fontWeight="700" opacity="0.95">
          {fmtY(value)} {unit}
        </text>
      </g>
    )
  }

  /* ── Live value at endpoint ── */
  const lastV  = vals[vals.length - 1]
  const lastX  = scX(data.length - 1)
  const lastY  = scY(lastV)

  /* ── Tooltip helper ── */
  const formatTooltipTime = (t) => {
    if (!t) return ''
    const d = new Date(t)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  }
  const threshDist = (v) => {
    const parts = []
    if (warnAt != null) parts.push(`Warn: ${(v - warnAt).toFixed(2)} ${unit}`)
    if (critAt != null) parts.push(`Crit: ${(v - critAt).toFixed(2)} ${unit}`)
    return parts.join('  ·  ')
  }

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ display: 'block', overflow: 'visible' }}
      role="img"
      aria-label={`${label} trend. Latest: ${lastV?.toFixed(2)} ${unit}`}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity={mini ? '0.20' : '0.30'} />
          <stop offset="80%"  stopColor={color} stopOpacity="0.04" />
          <stop offset="100%" stopColor={color} stopOpacity="0.00" />
        </linearGradient>
        <clipPath id={clipId}>
          <rect x={PAD.left} y={PAD.top} width={cW} height={cH} />
        </clipPath>
      </defs>

      {!mini && (
        <>
          {/* ── Background fill ── */}
          <rect x={PAD.left} y={PAD.top} width={cW} height={cH}
            fill="var(--bg-raised,#1e2535)" opacity="0.35" rx="2" />

          {/* ── Horizontal grid lines ── */}
          {yTicks.map(({ y }, i) => (
            <line key={i}
              x1={PAD.left} y1={y} x2={PAD.left + cW} y2={y}
              stroke="var(--border,#2e3a52)"
              strokeWidth={i === 0 || i === N_YTICK - 1 ? 1.2 : 0.7}
              strokeDasharray={i === 0 || i === N_YTICK - 1 ? 'none' : '4 4'}
            />
          ))}

          {/* ── Y-axis spine ── */}
          <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + cH}
            stroke="var(--border-md,#3d4f6e)" strokeWidth="1.4" />

          {/* ── X-axis spine ── */}
          <line x1={PAD.left} y1={PAD.top + cH} x2={PAD.left + cW} y2={PAD.top + cH}
            stroke="var(--border-md,#3d4f6e)" strokeWidth="1.4" />

          {/* ── Y-axis tick marks & labels ── */}
          {yTicks.map(({ v, y }, i) => (
            <g key={i}>
              <line x1={PAD.left - 6} y1={y} x2={PAD.left} y2={y}
                stroke="var(--border-md,#3d4f6e)" strokeWidth="1.5" />
              <text x={PAD.left - 11} y={y}
                textAnchor="end" dominantBaseline="middle"
                fill="var(--txt-2,#94a3b8)" fontSize="16" fontFamily="JetBrains Mono,monospace" fontWeight="500">
                {fmtY(v)}
              </text>
            </g>
          ))}

          {/* ── Y-axis title (rotated) ── */}
          <text
            x={18} y={PAD.top + cH / 2}
            textAnchor="middle" dominantBaseline="middle"
            fill="var(--txt,#e2e8f0)" fontSize="15" fontFamily="Inter,sans-serif" fontWeight="700"
            transform={`rotate(-90, 18, ${PAD.top + cH / 2})`}
          >
            {label}{unit ? ` (${unit})` : ''}
          </text>

          {/* ── X-axis tick marks & labels ── */}
          {xTicks.map(({ idx, x, lbl }) => (
            <g key={idx}>
              <line x1={x} y1={PAD.top + cH} x2={x} y2={PAD.top + cH + 7}
                stroke="var(--border-md,#3d4f6e)" strokeWidth="1.5" />
              <text x={x} y={PAD.top + cH + 24}
                textAnchor="middle"
                fill="var(--txt-2,#94a3b8)" fontSize="15" fontFamily="JetBrains Mono,monospace" fontWeight="500">
                {lbl}
              </text>
            </g>
          ))}

          {/* ── X-axis title ── */}
          <text
            x={PAD.left + cW / 2} y={H - 8}
            textAnchor="middle"
            fill="var(--txt-2,#94a3b8)" fontSize="14" fontFamily="Inter,sans-serif" fontWeight="600"
          >
            Elapsed Time — most recent at right (ISO 13373-3)
          </text>
        </>
      )}

      {/* ── Threshold reference lines ── */}
      {threshLine(warnAt, '#fbbf24')}
      {threshLine(critAt, '#ef4444')}

      {/* ── Area fill ── */}
      <path d={areaPath} fill={`url(#${gradId})`} clipPath={`url(#${clipId})`} />

      {/* ── Trend line ── */}
      <path d={linePath} fill="none" stroke={color}
        strokeWidth={mini ? 1.5 : 2.2}
        strokeLinecap="round" strokeLinejoin="round"
        clipPath={`url(#${clipId})`} />

      {/* ── Min / Max annotations ── */}
      {!mini && rawMax !== rawMin && (
        <>
          <text x={scX(maxIdx)} y={scY(rawMax) - 14}
            textAnchor="middle" fill={color}
            fontSize="14" fontFamily="JetBrains Mono,monospace" fontWeight="700" opacity="0.9">
            ▲ {fmtY(rawMax)}
          </text>
          <text x={scX(minIdx)} y={scY(rawMin) + 22}
            textAnchor="middle" fill="var(--txt-2,#94a3b8)"
            fontSize="14" fontFamily="JetBrains Mono,monospace" fontWeight="600" opacity="0.85">
            ▼ {fmtY(rawMin)}
          </text>
        </>
      )}

      {/* ── Live endpoint ── */}
      <circle cx={lastX} cy={lastY}
        r={mini ? 3 : 5}
        fill={color}
        stroke="var(--bg-surface,#161b25)"
        strokeWidth={mini ? 1.5 : 2.5}
      />
      {!mini && (
        <text x={lastX + 10} y={lastY}
          dominantBaseline="middle"
          fill={color} fontSize="16" fontFamily="JetBrains Mono,monospace" fontWeight="700">
          {fmtY(lastV)} {unit}
        </text>
      )}

      {/* ── Interactive hover overlay (non-mini) ── */}
      {!mini && (
        <>
          {/* Transparent overlay rects for hover detection */}
          {vals.map((v, i) => {
            const x = scX(i)
            const hw = i === 0 ? cW / (data.length * 2)
              : i === data.length - 1 ? cW / (data.length * 2)
              : cW / data.length
            return (
              <rect
                key={i}
                x={x - hw / 2}
                y={PAD.top}
                width={hw}
                height={cH}
                fill="transparent"
                style={{ cursor: 'crosshair' }}
                onMouseEnter={() => setTooltip({ i, v, t: toT(data[i]), x, y: scY(v) })}
                onMouseLeave={() => setTooltip(null)}
              />
            )
          })}

          {/* Tooltip */}
          {tooltip && (() => {
            const tx = Math.min(tooltip.x + 10, W - 160)
            const ty = Math.max(PAD.top + 2, tooltip.y - 36)
            return (
              <g>
                {/* vertical crosshair */}
                <line x1={tooltip.x} y1={PAD.top} x2={tooltip.x} y2={PAD.top + cH}
                  stroke={color} strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                <circle cx={tooltip.x} cy={tooltip.y} r="4" fill={color}
                  stroke="var(--bg-surface,#161b25)" strokeWidth="2" />
                {/* box */}
                <rect x={tx - 4} y={ty - 4} width="170" height="42" rx="4"
                  fill="var(--bg-raised,#1e2535)" stroke="var(--border-md,#3d4f6e)" strokeWidth="1" opacity="0.97" />
                <text x={tx + 2} y={ty + 11} fill="var(--txt,#e2e8f0)"
                  fontSize="10" fontFamily="JetBrains Mono,monospace" fontWeight="700">
                  {fmtY(tooltip.v)} {unit}
                </text>
                {tooltip.t && (
                  <text x={tx + 2} y={ty + 24} fill="var(--txt-3,#64748b)"
                    fontSize="9.5" fontFamily="JetBrains Mono,monospace">
                    {formatTooltipTime(tooltip.t)}
                  </text>
                )}
                {(warnAt != null || critAt != null) && (
                  <text x={tx + 2} y={ty + 36} fill="var(--txt-3,#64748b)"
                    fontSize="8.5" fontFamily="JetBrains Mono,monospace">
                    {threshDist(tooltip.v)}
                  </text>
                )}
              </g>
            )
          })()}
        </>
      )}
    </svg>
  )
}
