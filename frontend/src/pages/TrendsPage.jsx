/**
 * TrendsPage
 * Full-screen tabbed trend display.
 * One parameter is shown at a time in a large professional chart.
 * Engineering thresholds per ISO 13373-3, IEC 60034-1, ISO 10816-3.
 */
import { useState, useMemo } from 'react'
import { TrendChart } from '../components/TrendChart.jsx'
import { CategoricalTrend } from '../components/CategoricalTrend.jsx'

/* Helper: extract plain value from {t,v} or plain number */
const toV = (p) => (p != null && typeof p === 'object' ? p.v : p)

/* ── Time windows ── */
const WINDOWS = [
  { label: '30 s',  value: '30s'  },
  { label: '5 min', value: '5m'   },
  { label: '15 min', value: '15m' },
  { label: '1 hr',  value: '1h'   },
  { label: '6 hr',  value: '6h'   },
]

/* ── Engineering metadata per parameter ── */
const PARAM_META = {
  vibration: {
    label: 'Vibration RMS',
    unit:  'g',
    color: '#f97316',
    warnAt: 5.0, critAt: 8.0,
    desc:  'Root Mean Square vibration acceleration — ISO 10816-3',
    refNote: 'Zone A (new) <2.3 g  ·  Zone B (acceptable) <4.5 g  ·  Zone C (alarm) <7.1 g  ·  Zone D (danger) ≥7.1 g',
  },
  temperature: {
    label: 'Stator Temperature',
    unit:  '°C',
    color: '#ef4444',
    warnAt: 95, critAt: 120,
    desc:  'Stator winding temperature — IEC 60034-1 Class F insulation (155 °C abs. limit)',
    refNote: 'Warning at 95 °C  ·  Critical at 120 °C  ·  Class F abs. limit: 155 °C  ·  Each 10 °C above rated halves insulation life',
  },
  current: {
    label: 'Phase U Current',
    unit:  'A',
    color: '#2563eb',
    warnAt: 33, critAt: 35,
    desc:  'Phase U stator current — IEC 60034-1  (Rated: 30 A, ±10%/±17% thresholds)',
    refNote: 'Warning at 33 A (+10% of 30 A rated)  ·  Critical at 35 A (+17% of rated)',
  },
  rpm: {
    label: 'Rotor Speed',
    unit:  'RPM',
    color: '#a78bfa',
    warnAt: 1550, critAt: 1600,
    desc:  'Motor rotor speed — 4-pole 50 Hz SCIM (Sync: 1500 RPM, Rated: 1480 RPM)',
    refNote: 'Rated: 1480 RPM  ·  Overspeed warn: >1550  ·  Overspeed crit: >1600  ·  Underspeed crit: <1350',
  },
  torque: {
    label: 'Shaft Torque',
    unit:  'N·m',
    color: '#38bdf8',
    warnAt: 110, critAt: 130,
    desc:  'Shaft mechanical torque — rated 97.3 N·m at 1480 RPM for 15 kW motor',
    refNote: 'Rated: 97.3 N·m  ·  Warning at 110 N·m (113%)  ·  Critical at 130 N·m (134%)',
  },
  rul: {
    label: 'Remaining Useful Life',
    unit:  'h',
    color: '#16a34a',
    warnAt: 150, critAt: 50,
    desc:  'Estimated hours of remaining useful operation before maintenance is required',
    refNote: 'Green >150 h  ·  Amber 50–150 h (plan maintenance)  ·  Red <50 h (immediate action required)',
  },
  predictionCertainty: {
    label: 'Prediction Certainty',
    unit:  '%',
    color: '#06b6d4',
    warnAt: null, critAt: null,
    desc:  'Per-inference softmax certainty of the current health classification. NOT the 90.67% published model accuracy.',
    refNote: 'Values >85% indicate high-certainty classification  ·  Below 60% treat result with caution  ·  Source: Meta-Fusion XGBoost',
  },
  health: {
    label: 'Health State',
    unit:  '',
    color: '#a855f7',
    warnAt: null, critAt: null,
    desc:  'Categorical health state — NORMAL / WARNING / CRITICAL — as classified by the meta-fusion model',
    refNote: 'NORMAL: all parameters within limits  ·  WARNING: developing degradation  ·  CRITICAL: immediate action required',
    categorical: true,
  },
}

/* ── Statistics calculator — operates on plain number arrays ── */
function calcStats(vals) {
  if (!vals || vals.length < 2) return null
  const n    = vals.length
  const min  = Math.min(...vals)
  const max  = Math.max(...vals)
  const mean = vals.reduce((s, v) => s + v, 0) / n
  const std  = Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / n)
  const last = vals[n - 1]
  const prev = vals[Math.max(0, n - Math.ceil(n * 0.1))]
  const trend = last > prev + std * 0.3 ? 'Rising ↑'
              : last < prev - std * 0.3 ? 'Falling ↓'
              : 'Stable →'
  const trendColor = trend.startsWith('Rising') ? 'var(--warn)'
    : trend.startsWith('Falling') ? 'var(--ok)'
    : 'var(--txt-3)'
  return { min, max, mean, std, last, trend, trendColor, n }
}

/* ── Health state stats ── */
function calcHealthStats(points) {
  if (!points || points.length < 1) return null
  const vals = points.map(toV)
  const counts = [0, 0, 0]
  vals.forEach((v) => { const i = Math.round(Math.max(0, Math.min(2, v))); counts[i]++ })
  const last = Math.round(Math.max(0, Math.min(2, vals[vals.length - 1])))
  const labels = ['NORMAL', 'WARNING', 'CRITICAL']
  return { counts, last, label: labels[last], n: vals.length }
}

/* ── Format number ── */
const fmt = (v, unit) => {
  if (v == null || isNaN(v)) return '—'
  const s = Math.abs(v) >= 100 ? v.toFixed(1) : Math.abs(v) >= 10 ? v.toFixed(2) : v.toFixed(3)
  return unit ? `${s} ${unit}` : s
}

function downloadCsv(points, meta, windowLabel) {
  const vals = points.map(toV)
  const BOM  = '﻿'
  const rows = [
    [`MotorGuard Trend Export — ${meta.label}`, '', ''],
    [`Window: ${windowLabel}`, `Unit: ${meta.unit || 'categorical'}`, `Samples: ${vals.length}`],
    ['Sample Index', `${meta.label}${meta.unit ? ` (${meta.unit})` : ''}`, 'Status'],
    ...vals.map((v, i) => {
      const st = meta.critAt != null && v >= meta.critAt ? 'CRITICAL'
               : meta.warnAt != null && v >= meta.warnAt ? 'WARNING' : 'NORMAL'
      return [i + 1, v?.toFixed(4) ?? '', st]
    }),
  ]
  const csv  = BOM + rows.map((r) => r.join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url
  a.download = `trend-${meta.label.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export function TrendsPage({ controller }) {
  const [activeKey,    setActiveKey]    = useState('vibration')
  const [activeWindow, setActiveWindow] = useState('15m')
  const { trendSeries, setTrendWindow } = controller

  const handleWindow = (w) => {
    setActiveWindow(w)
    if (setTrendWindow) setTrendWindow(w)
  }

  /* Map series by key */
  const seriesMap = Object.fromEntries((trendSeries ?? []).map((s) => [s.key, s]))

  /* Active series */
  const activeSeries = seriesMap[activeKey]
  const points       = activeSeries?.points ?? []
  const meta         = PARAM_META[activeKey] ?? { label: activeKey, unit: '', color: '#0ea5e9' }
  const isHealth     = meta.categorical === true

  /* Stats — extracted from {t,v} or plain number arrays */
  const stats = useMemo(() => {
    if (isHealth) return null
    return calcStats(points.map(toV))
  }, [points, isHealth])

  const healthStats = useMemo(() => {
    if (!isHealth) return null
    return calcHealthStats(points)
  }, [points, isHealth])

  /* Status derived from latest value */
  const statusCls = useMemo(() => {
    if (!stats || meta.critAt == null) return 'ok'
    if (stats.last >= meta.critAt) return 'crit'
    if (meta.warnAt && stats.last >= meta.warnAt) return 'warn'
    return 'ok'
  }, [stats, meta])

  const windowLabel = WINDOWS.find((w) => w.value === activeWindow)?.label ?? activeWindow

  return (
    <div className="trends-fullscreen">

      {/* ── Top control bar ── */}
      <div className="trends-control-bar">
        <div className="trends-title-block">
          <span className="page-title">Trend Analysis</span>
          <span className="page-sub">
            {meta.label} &nbsp;·&nbsp; Window: {windowLabel}
            &nbsp;·&nbsp;
            {points.length > 0
              ? <span style={{ color: 'var(--ok)', fontWeight: 600 }}>● {points.length} samples</span>
              : <span style={{ color: 'var(--txt-3)' }}>Awaiting data…</span>
            }
          </span>
        </div>

        {/* Window selector */}
        <div className="trends-window-group">
          <span className="trends-ctrl-label">Window</span>
          <div className="trends-btn-group">
            {WINDOWS.map((w) => (
              <button
                key={w.value}
                className={`filter-btn${activeWindow === w.value ? ' active' : ''}`}
                onClick={() => handleWindow(w.value)}
              >
                {w.label}
              </button>
            ))}
          </div>
        </div>

        {/* Export trend data */}
        {points.length > 0 && (
          <button
            className="btn btn-ghost trends-export-btn"
            onClick={() => downloadCsv(points, meta, windowLabel)}
            title="Export current trend data as CSV"
          >
            ↓ Export CSV
          </button>
        )}
      </div>

      {/* ── Parameter tabs ── */}
      <div className="trends-tab-row">
        {Object.entries(PARAM_META).map(([key, m]) => {
          const s    = seriesMap[key]
          const last = s?.points?.at(-1)
          const lastVal = last != null ? toV(last) : null
          const isActive = key === activeKey
          return (
            <button
              key={key}
              className={`trend-tab${isActive ? ' trend-tab-active' : ''}`}
              onClick={() => setActiveKey(key)}
              style={isActive ? { borderBottomColor: m.color, color: m.color } : {}}
              aria-pressed={isActive}
            >
              <span className="trend-tab-dot" style={{ background: m.color }} />
              <span className="trend-tab-label">{m.label}</span>
              {lastVal != null && !m.categorical && (
                <span className="trend-tab-val" style={{ color: isActive ? m.color : undefined }}>
                  {fmt(lastVal, m.unit)}
                </span>
              )}
              {lastVal != null && m.categorical && (
                <span className="trend-tab-val" style={{ color: isActive ? m.color : undefined }}>
                  {['NRM', 'WARN', 'CRIT'][Math.round(Math.max(0, Math.min(2, lastVal)))] ?? '—'}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* ── Chart area ── */}
      <div className="trends-chart-shell">
        {/* Parameter description bar */}
        <div className="trends-param-info">
          <div className="trends-param-desc">{meta.desc}</div>
          <div className="trends-param-ref">{meta.refNote}</div>
        </div>

        {/* The actual chart — fills the full viewport height */}
        <div className="trends-chart-viewport">
          {isHealth ? (
            <CategoricalTrend data={points} height={600} />
          ) : (
            <TrendChart
              data={points}
              color={meta.color}
              unit={meta.unit}
              label={meta.label}
              height={600}
              warnAt={meta.warnAt}
              critAt={meta.critAt}
            />
          )}
        </div>
      </div>

      {/* ── Statistics panel ── */}
      <div className="trends-stats-bar">
        {isHealth && healthStats ? (
          <>
            <div className={`trends-stat-main trends-stat-${{ 0: 'ok', 1: 'warn', 2: 'crit' }[healthStats.last] ?? 'ok'}`}>
              <span className="trends-stat-main-label">Current</span>
              <span className="trends-stat-main-val" style={{ color: meta.color }}>
                {healthStats.label}
              </span>
            </div>
            {[
              { label: 'NORMAL',   val: `${healthStats.counts[0]} samples`, color: '#22c55e' },
              { label: 'WARNING',  val: `${healthStats.counts[1]} samples`, color: '#f59e0b' },
              { label: 'CRITICAL', val: `${healthStats.counts[2]} samples`, color: '#ef4444' },
              { label: 'Total',    val: healthStats.n },
              { label: 'Window',   val: windowLabel },
            ].map(({ label, val, color }) => (
              <div key={label} className="trends-stat-item">
                <span className="trends-stat-label">{label}</span>
                <span className="trends-stat-val" style={color ? { color } : undefined}>{val}</span>
              </div>
            ))}
          </>
        ) : stats ? (
          <>
            <div className={`trends-stat-main trends-stat-${statusCls}`}>
              <span className="trends-stat-main-label">Current</span>
              <span className="trends-stat-main-val" style={{ color: meta.color }}>
                {fmt(stats.last, meta.unit)}
              </span>
            </div>
            {[
              { label: 'Mean',    val: fmt(stats.mean, meta.unit) },
              { label: 'Min',     val: fmt(stats.min,  meta.unit), color: 'var(--ok)'   },
              { label: 'Max',     val: fmt(stats.max,  meta.unit), color: 'var(--warn)' },
              { label: 'StdDev',  val: fmt(stats.std,  meta.unit) },
              { label: 'Trend',   val: stats.trend, color: stats.trendColor },
              { label: 'Samples', val: stats.n },
              { label: 'Window',  val: windowLabel },
            ].map(({ label, val, color }) => (
              <div key={label} className="trends-stat-item">
                <span className="trends-stat-label">{label}</span>
                <span className="trends-stat-val" style={color ? { color } : undefined}>{val}</span>
              </div>
            ))}

            {/* Threshold indicators */}
            {meta.warnAt != null && (
              <div className="trends-stat-item">
                <span className="trends-stat-label">Warn at</span>
                <span className="trends-stat-val" style={{ color: '#fbbf24' }}>{fmt(meta.warnAt, meta.unit)}</span>
              </div>
            )}
            {meta.critAt != null && (
              <div className="trends-stat-item">
                <span className="trends-stat-label">Crit at</span>
                <span className="trends-stat-val" style={{ color: '#ef4444' }}>{fmt(meta.critAt, meta.unit)}</span>
              </div>
            )}
          </>
        ) : (
          <span className="trends-no-data">No data — start MATLAB/Simulink to populate trends</span>
        )}
      </div>

    </div>
  )
}
