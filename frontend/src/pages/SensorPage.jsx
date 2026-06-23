/**
 * SensorPage — Live Sensors
 * Full-page layout with:
 *   • 4-gauge row (RPM / Torque / Vibration / Stator Temp)
 *   • Real-time mini-charts for those gauges
 *   • 3-phase current card
 *   • Sensor detail table for all mechanical/thermal channels
 *   • Supply parameters block
 */
import { useState, useEffect } from 'react'
import { SensorCard }     from '../components/SensorCard.jsx'
import { GaugeRing }      from '../components/GaugeRing.jsx'
import { ThreePhaseCard } from '../components/ThreePhaseCard.jsx'
import { TrendChart }     from '../components/TrendChart.jsx'

function sensorStatus(value, warnAt, critAt) {
  if (value == null || isNaN(value)) return 'idle'   // no data — neutral, not green
  if (value >= critAt) return 'crit'
  if (value >= warnAt) return 'warn'
  return 'ok'
}

/* ── Mini sparkline card ── */
function SparkCard({ label, unit, value, points, color, warnAt, critAt, status }) {
  const last = typeof value === 'number' && !isNaN(value) ? value : (points?.at(-1) ?? null)
  const displayVal = last != null ? (last < 10 ? last.toFixed(2) : last.toFixed(1)) : '—'
  return (
    <div className={`spark-card spark-${status}`}>
      <div className="spark-card-top">
        <span className="spark-label">{label}</span>
        <span className="spark-value" style={{ color }}>
          {displayVal}
          <span className="spark-unit">{unit}</span>
        </span>
      </div>
      <div className="spark-chart-area">
        <TrendChart
          data={points ?? []}
          color={color}
          unit={unit}
          label={label}
          height={500}
          warnAt={warnAt}
          critAt={critAt}
        />
      </div>
    </div>
  )
}

export function SensorPage({ controller }) {
  const { sensors, signalQuality, operatingPoint, trendSeries } = controller

  /* Last update timestamp — ticks every second when data is arriving */
  const [lastUpdate, setLastUpdate] = useState(null)
  useEffect(() => {
    if (sensors && Object.keys(sensors).length > 0) {
      setLastUpdate(new Date())
    }
  }, [sensors])

  const lastUpdateStr = lastUpdate
    ? `Last updated: ${lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}`
    : 'Awaiting first data packet…'

  const vib   = sensors?.vibration    ?? {}
  const temp  = sensors?.temperature  ?? {}
  const cur   = sensors?.phaseCurrent ?? {}
  const therm = sensors?.thermal      ?? {}

  const rpm    = parseFloat(operatingPoint?.rpm)
  const torque = parseFloat(operatingPoint?.torque)

  const qualityLabel = signalQuality?.signalQuality ?? 'unknown'
  const qualityColor = qualityLabel === 'nominal' ? 'var(--ok)' : qualityLabel === 'degraded' ? 'var(--warn)' : 'var(--txt-3)'

  /* Trend series keyed by name */
  const series = Object.fromEntries((trendSeries ?? []).map((s) => [s.key, s]))

  /* Mechanical detail channels */
  // Thresholds per IEC 60034-1 (thermal), ISO 10816-3 (vibration), IEC 60034-14 (bearings)
  const mechanicalChannels = [
    { name: 'Vibration RMS',   value: vib.rms,         unit: 'g',   min: 0,  max: 15,  warnAt: 5,   critAt: 8,   std: 'ISO 10816-3 Zone B/C boundary: 5 g' },
    { name: 'Crest Factor',    value: vib.crestFactor,  unit: '',    min: 0,  max: 12,  warnAt: 6,   critAt: 9,   std: 'Normal: <4.0; Bearing fault: >6' },
    { name: 'Kurtosis',        value: vib.kurtosis,     unit: '',    min: 0,  max: 20,  warnAt: 8,   critAt: 12,  std: 'ISO 13373-3: Healthy≈3; Fault>8' },
    { name: 'Stator Temp',     value: temp.stator,      unit: '°C',  min: 20, max: 160, warnAt: 95,  critAt: 120, std: 'IEC 60034-1 Class F: 155 °C limit' },
    { name: 'Bearing Temp',    value: temp.bearing,     unit: '°C',  min: 20, max: 120, warnAt: 80,  critAt: 100, std: 'IEC 60034-14: Warn 80 °C / Crit 100 °C' },
    { name: 'Temp Delta',      value: temp.delta,       unit: 'K',   min: 0,  max: 120, warnAt: 50,  critAt: 70,  std: 'IEC 60034-1 Class F rise limit: 105 K' },
    { name: 'Thermal Hotspot', value: therm.hotSpot,    unit: '°C',  min: 20, max: 160, warnAt: 95,  critAt: 120, std: 'IR thermography hotspot — IEC 60034-1' },
  ]

  return (
    <div className="sensor-page-shell">
      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <div className="page-title">Live Sensors</div>
          <div className="page-sub">Real-time readings from motor-pump instrumentation</div>
          <div className="sensor-last-update">{lastUpdateStr}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'var(--txt-3)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Signal quality</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: qualityColor }}>{qualityLabel}</span>
          <span style={{ fontSize: 11, color: sensors?._stale ? 'var(--warn)' : 'var(--txt-3)', marginLeft: 4 }}>
            {sensors?.freshness || ''}
          </span>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          SECTION 1 — Primary gauges + real-time sparklines
      ══════════════════════════════════════════════════════════ */}
      <div className="section-header mb-12">
        <span className="section-title">Primary Parameters</span>
        <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>Click trend arrows to jump to full analysis →</span>
      </div>

      {/* 4-column gauge row */}
      <div className="sensor-gauge-grid">
        {/* Rotor Speed */}
        <div className="gauge-card">
          <div className="gauge-card-top">
            <GaugeRing
              value={!isNaN(rpm) ? rpm : 0}
              max={1800}
              unit="RPM"
              label="Rotor Speed"
              status={!isNaN(rpm) && rpm > 1600 ? 'crit' : !isNaN(rpm) && rpm > 1550 ? 'warn' : !isNaN(rpm) && rpm < 1350 ? 'crit' : !isNaN(rpm) && rpm < 1400 ? 'warn' : 'ok'}
              size={100}
            />
          </div>
          <div className="gauge-meta">
            <span>Rated: 1480 RPM | Warn: &gt;1550 | Crit: &gt;1600</span>
            <span>Slip: {!isNaN(rpm) ? ((1500 - rpm) / 1500 * 100).toFixed(2) : '--'}%</span>
          </div>
        </div>

        {/* Shaft Torque */}
        <div className="gauge-card">
          <div className="gauge-card-top">
            <GaugeRing
              value={!isNaN(torque) ? torque : 0}
              max={160}
              unit="N·m"
              label="Shaft Torque"
              status={!isNaN(torque) && torque > 130 ? 'crit' : !isNaN(torque) && torque > 110 ? 'warn' : 'ok'}
              size={100}
            />
          </div>
          <div className="gauge-meta">
            <span>Rated: 97.3 N·m | Warn: &gt;110 | Crit: &gt;130</span>
            <span>Load: {!isNaN(torque) ? ((torque / 97.3) * 100).toFixed(1) : '--'}%</span>
          </div>
        </div>

        {/* Vibration RMS */}
        <div className="gauge-card">
          <div className="gauge-card-top">
            <GaugeRing
              value={vib.rms ?? 0}
              max={10}
              unit="g"
              label="Vibration RMS"
              status={sensorStatus(vib.rms, 5, 8)}
              size={100}
            />
          </div>
          <div className="gauge-meta">
            <span>ISO 10816 Zone A: &lt;2.3 g</span>
            <span>Kurtosis: {vib.kurtosis?.toFixed(2) ?? '--'}</span>
          </div>
        </div>

        {/* Stator Temp */}
        <div className="gauge-card">
          <div className="gauge-card-top">
            <GaugeRing
              value={temp.stator ?? 0}
              max={160}
              unit="°C"
              label="Stator Temp"
              status={sensorStatus(temp.stator, 95, 120)}
              size={100}
            />
          </div>
          <div className="gauge-meta">
            <span>Class F limit: 155 °C</span>
            <span>Bearing: {temp.bearing?.toFixed(1) ?? '--'} °C</span>
          </div>
        </div>
      </div>

      {/* Real-time trend charts (matched to gauges above) */}
      <div className="sensor-spark-grid">
        {/* IEC/ISO standard thresholds applied to all 4 primary trend cards */}
        <SparkCard
          label="Rotor Speed" unit="RPM"
          value={!isNaN(rpm) ? rpm : null}
          points={series.rpm?.points ?? []}
          color="#a78bfa"
          warnAt={1550} critAt={1600}
          status={isNaN(rpm) ? 'idle' : rpm > 1600 ? 'crit' : rpm > 1550 ? 'warn' : rpm < 1350 ? 'crit' : rpm < 1400 ? 'warn' : 'ok'}
        />
        <SparkCard
          label="Shaft Torque" unit="N·m"
          value={!isNaN(torque) ? torque : null}
          points={series.torque?.points ?? []}
          color="#38bdf8"
          warnAt={110} critAt={130}
          status={isNaN(torque) ? 'idle' : torque > 130 ? 'crit' : torque > 110 ? 'warn' : 'ok'}
        />
        <SparkCard
          label="Vibration RMS" unit="g"
          value={vib.rms}
          points={series.vibration?.points ?? []}
          color="#f97316"
          warnAt={5} critAt={8}
          status={sensorStatus(vib.rms, 5, 8)}
        />
        <SparkCard
          label="Stator Temp" unit="°C"
          value={temp.stator}
          points={series.temperature?.points ?? []}
          color="#ef4444"
          warnAt={95} critAt={120}
          status={sensorStatus(temp.stator, 95, 120)}
        />
      </div>

      {/* ══════════════════════════════════════════════════════════
          SECTION 2 — 3-Phase current + additional charts
      ══════════════════════════════════════════════════════════ */}
      <div className="section-header mb-12">
        <span className="section-title">3-Phase Stator Current</span>
        <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>IEC 60446 colour code — 400 V / 50 Hz / 3&#934;</span>
      </div>

      <div className="sensor-current-row">
        <ThreePhaseCard
          u={cur.u} v={cur.v} w={cur.w}
          imbalance={cur.imbalance}
          voltage={400}
          frequency={50}
        />

        {/* Phase U live chart */}
        <div className="card sensor-current-chart">
          <div className="card-header">
            <span className="card-title">Phase U Current — Live</span>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
              {cur.u?.toFixed(2) ?? '—'} A
            </span>
          </div>
          <div style={{ padding: '8px 12px 12px' }}>
            <TrendChart
              data={series.current?.points ?? []}
              color="#2563eb"
              unit="A"
              label="Phase U Current"
              height={500}
              warnAt={33}
              critAt={35}
            />
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          SECTION 3 — Detail sensor table
      ══════════════════════════════════════════════════════════ */}
      <div className="section-header mb-12">
        <span className="section-title">Mechanical & Thermal Detail</span>
        <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>All channels — warning / critical limits per IEC/ISO standards</span>
      </div>

      <div className="card" style={{ overflowX: 'auto', marginBottom: 20 }}>
        <table className="sensor-table" aria-label="Sensor readings">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Value</th>
              <th>Unit</th>
              <th>Warn Limit</th>
              <th>Crit Limit</th>
              <th>Status</th>
              <th>Standard</th>
            </tr>
          </thead>
          <tbody>
            {mechanicalChannels.map((ch) => {
              const st = sensorStatus(ch.value, ch.warnAt, ch.critAt)
              return (
                <tr key={ch.name}>
                  <td style={{ fontWeight: 600, color: 'var(--txt)' }}>{ch.name}</td>
                  <td
                    style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: 14 }}
                    aria-live="polite"
                    aria-atomic="true"
                    aria-label={`${ch.name}: ${ch.value?.toFixed(2) ?? '—'} ${ch.unit}`}
                  >
                    {typeof ch.value === 'number' && !isNaN(ch.value) ? ch.value.toFixed(2) : '—'}
                  </td>
                  <td style={{ color: 'var(--txt-3)', fontFamily: 'var(--mono)' }}>{ch.unit}</td>
                  <td style={{ color: 'var(--warn)', fontFamily: 'var(--mono)' }}>{ch.warnAt}</td>
                  <td style={{ color: 'var(--crit)', fontFamily: 'var(--mono)' }}>{ch.critAt}</td>
                  <td>
                    <span className={`sensor-status-pill sensor-status-${st}`}>
                      {st === 'ok' ? '● OK' : st === 'warn' ? '▲ WARN' : '■ CRIT'}
                    </span>
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--txt-3)', maxWidth: 200 }}>{ch.std}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* ══════════════════════════════════════════════════════════
          SECTION 4 — Supply parameters
      ══════════════════════════════════════════════════════════ */}
      <div className="section-header mb-12">
        <span className="section-title">Supply Parameters</span>
        <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>Nominal grid values — not dynamically measured</span>
      </div>

      <div className="sensor-supply-grid">
        {[
          { label: 'Supply Frequency', value: '50.00', unit: 'Hz', color: '#a78bfa', note: 'Grid nominal' },
          { label: 'Line Voltage',     value: '400',   unit: 'V',  color: '#0ea5e9', note: 'L-L (3Ø)' },
          { label: 'Phase Voltage',    value: '231',   unit: 'V',  color: '#0ea5e9', note: 'L-N' },
          { label: 'Pole Pairs',       value: '2',     unit: 'p',  color: '#64748b', note: '4-pole motor' },
          { label: 'Sync Speed',       value: '1500',  unit: 'RPM',color: '#a78bfa', note: 'Ns = 60f/p' },
          { label: 'Power Class',      value: 'IE3',   unit: '',   color: '#16a34a', note: 'Premium efficiency' },
        ].map(({ label, value, unit, color, note }) => (
          <div key={label} className="card supply-param-card">
            <div style={{ fontSize: 10, color: 'var(--txt-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>{label}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 4 }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 24, fontWeight: 700, color }}>{value}</span>
              <span style={{ fontSize: 12, color: 'var(--txt-3)' }}>{unit}</span>
            </div>
            <div style={{ fontSize: 10, color: 'var(--txt-3)' }}>{note}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
