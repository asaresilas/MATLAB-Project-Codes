import { MotorPumpSchematic } from '../components/MotorPumpSchematic.jsx'
import { MetricCard } from '../components/MetricCard.jsx'
import { TrendChart } from '../components/TrendChart.jsx'
import { ThreePhaseCard } from '../components/ThreePhaseCard.jsx'
import { OperatingPointCard } from '../components/OperatingPointCard.jsx'

export function DashboardPage({ controller }) {
  const { machine, recommendation, sensors, trendSeries, alarms, operatingPoint, application } = controller
  const connectionState = application?.connectionState || 'booting'

  const healthState = machine?.healthState || 'unknown'
  const healthClass = {
    NORMAL:   'normal',
    WARNING:  'warning',
    CRITICAL: 'critical',
  }[healthState?.toUpperCase()] || 'unknown'

  // machine.predictionCertainty is the per-inference softmax probability stored as 0–100 %.
  // It is NOT the 90.67 % published model accuracy.
  const predictionCertainty = machine?.predictionCertainty != null
    ? `${parseFloat(machine.predictionCertainty).toFixed(1)}%`
    : '—'

  // Show '—' when RUL is null (no data received yet), not '0.0'.
  const rulHours = machine?.rulHours != null
    ? parseFloat(machine.rulHours).toFixed(1)
    : '—'
  const rulNum    = machine?.rulHours != null ? parseFloat(machine.rulHours) : NaN
  const rulStatus = isNaN(rulNum) ? 'idle'
    : rulNum < 50  ? 'crit'
    : rulNum < 150 ? 'warn'
    : 'ok'

  /* Sensor values */
  const tempVal   = sensors?.temperature?.stator
  const vibRms    = sensors?.vibration?.rms
  const currentU  = sensors?.phaseCurrent?.u
  const currentV  = sensors?.phaseCurrent?.v
  const currentW  = sensors?.phaseCurrent?.w
  const imbalance = sensors?.phaseCurrent?.imbalance

  // IEC 60034-1 Class F insulation: warn > 95 °C, critical > 120 °C
  const tempStatus = tempVal == null ? 'accent' : tempVal > 120 ? 'crit' : tempVal > 95 ? 'warn' : 'ok'
  const vibStatus  = vibRms  == null ? 'accent' : vibRms  > 8  ? 'crit' : vibRms  > 5  ? 'warn' : 'ok'

  /* Trend series */
  const vibSeries  = trendSeries?.find?.((t) => t.key === 'vibration')?.points  ?? []
  const tempSeries = trendSeries?.find?.((t) => t.key === 'temperature')?.points ?? []

  const activeCount = alarms?.active?.length ?? 0

  return (
    <div className="dash-grid">

      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <div className="page-title">System Overview</div>
          <div className="page-sub">Real-time motor-pump health dashboard</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {activeCount > 0 && (
            <span style={{ fontSize: 12, color: 'var(--crit)', fontWeight: 600 }}>
              {activeCount} active alarm{activeCount !== 1 ? 's' : ''}
            </span>
          )}
          <span className={`health-badge ${healthClass}`} role="status" aria-live="polite">
            <span className="health-dot" />
            {healthState?.toUpperCase() || 'UNKNOWN'}
          </span>
        </div>
      </div>

      {/* ── Awaiting-data banner — shown until first MATLAB packet arrives ── */}
      {connectionState === 'connected' && (
        <div style={{
          background: 'rgba(37, 99, 235, 0.08)',
          border: '1px solid rgba(37,99,235,0.25)',
          borderRadius: 8,
          padding: '10px 16px',
          fontSize: 13,
          color: 'var(--txt-2)',
        }}>
          ⋯ Connected to backend — waiting for MATLAB/Simulink to send data. Run your Simulink model to see live results here.
        </div>
      )}

      {/* ── Motor-pump schematic (full width) ── */}
      <div className="dash-motor-card">
        <div className="dash-motor-header">
          <span className="dash-motor-title">Motor-Pump Assembly</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>
              Prediction Certainty&nbsp;<strong style={{ color: 'var(--txt)' }}>{predictionCertainty}</strong>
              <span style={{ fontSize: 10, color: 'var(--txt-3)', marginLeft: 4 }}>(per inference)</span>
            </span>
            <span style={{ fontSize: 10, color: 'var(--txt-3)', fontFamily: 'var(--mono)' }}>
              ID: {machine?.machineId || '—'}
            </span>
          </div>
        </div>
        <MotorPumpSchematic healthState={healthState} />
        {recommendation && (
          <div style={{
            padding: '10px 18px',
            borderTop: '1px solid var(--border)',
            fontSize: 12.5,
            color: 'var(--txt-2)',
            lineHeight: 1.55,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
          }}>
            <span style={{ fontSize: 10, color: 'var(--txt-3)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', paddingTop: 2, flexShrink: 0 }}>
              Action
            </span>
            <span>{recommendation}</span>
          </div>
        )}
      </div>

      {/* ── Second row: 3-phase | operating point ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 14 }}>
        <ThreePhaseCard
          u={currentU}
          v={currentV}
          w={currentW}
          imbalance={imbalance}
          voltage={400}
          frequency={50}
        />
        <OperatingPointCard
          operatingPoint={operatingPoint}
          machine={machine}
        />
      </div>

      {/* ── KPI metric cards ── */}
      <div className="dash-kpi-grid">
        <MetricCard
          label="Remaining Useful Life"
          value={rulHours}
          unit="h"
          sub="Time to maintenance"
          status={rulStatus}
        />
        <MetricCard
          label="Motor Temperature"
          value={tempVal != null ? tempVal.toFixed(1) : '—'}
          unit="°C"
          sub="Stator winding"
          status={tempStatus}
        />
        <MetricCard
          label="Vibration RMS"
          value={vibRms != null ? vibRms.toFixed(3) : '—'}
          unit="g"
          sub="Bearing acceleration"
          status={vibStatus}
        />
        <MetricCard
          label="Phase Imbalance"
          value={imbalance != null ? imbalance.toFixed(2) : '—'}
          unit="%"
          sub="Max–min / avg × 100"
          status={imbalance == null ? 'idle' : imbalance > 15 ? 'crit' : imbalance > 8 ? 'warn' : 'ok'}
        />
      </div>

      {/* ── Trend charts (engineering standard — ISO 10816-3 / IEC 60034-1) ── */}
      <div className="dash-spark-grid">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Vibration RMS Trend</span>
            <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>
              ISO 10816-3 &nbsp;·&nbsp; {vibSeries.length} samples
            </span>
          </div>
          <div style={{ padding: '10px 14px 14px' }}>
            <TrendChart
              data={vibSeries}
              color="#f97316"
              unit="g"
              label="Vibration RMS"
              height={420}
              warnAt={5}
              critAt={8}
            />
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Stator Temperature Trend</span>
            <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>
              IEC 60034-1 Class F &nbsp;·&nbsp; {tempSeries.length} samples
            </span>
          </div>
          <div style={{ padding: '10px 14px 14px' }}>
            <TrendChart
              data={tempSeries}
              color="#ef4444"
              unit="°C"
              label="Stator Temp"
              height={420}
              warnAt={95}
              critAt={120}
            />
          </div>
        </div>
      </div>

    </div>
  )
}
