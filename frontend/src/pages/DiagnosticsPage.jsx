/**
 * DiagnosticsPage — AI Diagnostic Results
 * Six-section layout:
 *   A. Motor Health Status Banner
 *   B. Three metric cards (Health State / Fault Type / RUL)
 *   C. AI Explanation Panel
 *   D. Per-Modality Expert Confidence bars
 *   E. Live Sensor Parameters table
 *   F. Connection Status Footer
 */
import './DiagnosticsPage.css'

const HEALTH_COLOR = { NORMAL: 'diag-normal', WARNING: 'diag-warning', CRITICAL: 'diag-critical', UNKNOWN: 'diag-unknown' }
const HEALTH_ICON  = { NORMAL: '✔', WARNING: '⚠', CRITICAL: '✖', UNKNOWN: '?' }

function pct(v) { return v != null && !isNaN(v) ? `${(v * 100).toFixed(1)} %` : '—' }
function fmt(v, dp = 1, unit = '') { return v != null && !isNaN(v) ? `${Number(v).toFixed(dp)}${unit ? ' ' + unit : ''}` : '—' }

/* ── A. Status Banner ─────────────────────────────────────────────────────── */
function StatusBanner({ healthState, faultTypeName, confidence, lastPacketText }) {
  const state = healthState || 'UNKNOWN'
  const cls   = HEALTH_COLOR[state] || 'diag-unknown'
  return (
    <div className={`diag-banner ${cls}`}>
      <span className="diag-banner-icon">{HEALTH_ICON[state] || '?'}</span>
      <div className="diag-banner-body">
        <div className="diag-banner-title">Motor Health: {state}</div>
        <div className="diag-banner-sub">
          {faultTypeName || 'Healthy'} &nbsp;·&nbsp; Confidence {typeof confidence === 'number' ? `${confidence.toFixed(1)} %` : '—'} &nbsp;·&nbsp; Updated {lastPacketText || '—'}
        </div>
      </div>
    </div>
  )
}

/* ── B. Metric Cards ──────────────────────────────────────────────────────── */
function MetricCard({ label, value, sub, color }) {
  return (
    <div className={`diag-metric-card diag-metric-${color}`}>
      <div className="diag-metric-label">{label}</div>
      <div className="diag-metric-value">{value}</div>
      {sub && <div className="diag-metric-sub">{sub}</div>}
    </div>
  )
}

/* ── C. AI Explanation Panel ─────────────────────────────────────────────── */
function ExplanationPanel({ explanation, modelUsed }) {
  if (!explanation) {
    return (
      <section className="diag-section">
        <h2 className="diag-section-title">AI Explanation</h2>
        <div className="diag-explanation diag-explanation-empty">
          Awaiting inference result — connect to the backend to receive an explanation.
        </div>
      </section>
    )
  }
  return (
    <section className="diag-section">
      <h2 className="diag-section-title">AI Explanation</h2>
      <div className="diag-explanation">
        <p>{explanation}</p>
        <div className="diag-explanation-source">Model: {modelUsed || 'Meta Fusion XGBoost'}</div>
      </div>
    </section>
  )
}

/* ── D. Expert Confidence Bars ────────────────────────────────────────────── */
function ConfidenceBar({ name, conf, available, predictedClass }) {
  const pctVal = conf != null ? Math.round(conf * 100) : 0
  const isAvail = available !== 'standby'
  const barColor = !isAvail ? '#6b7280' : pctVal >= 80 ? '#16a34a' : pctVal >= 50 ? '#f59e0b' : '#dc2626'
  return (
    <div className={`diag-conf-row ${!isAvail ? 'diag-conf-standby' : ''}`}>
      <div className="diag-conf-name">{name}</div>
      <div className="diag-conf-bar-wrap">
        <div className="diag-conf-bar" style={{ width: `${pctVal}%`, background: barColor }} />
      </div>
      <div className="diag-conf-pct">{isAvail ? `${pctVal} %` : 'standby'}</div>
      <div className="diag-conf-class">{isAvail ? (predictedClass || '—') : '—'}</div>
    </div>
  )
}

function ExpertPanel({ models }) {
  const experts = [
    { key: 'CWRU',       label: 'Vibration — CWRU-CNN' },
    { key: 'Induction',  label: 'Vibration — Induction-CNN' },
    { key: 'NASA',       label: 'RUL — NASA Bi-LSTM-Attn' },
    { key: 'Current',    label: 'Current — 3-Phase CNN' },
    { key: 'Thermal',    label: 'Thermal — MobileNetV2' },
    { key: 'Fusion',     label: 'Meta-Fusion — XGBoost' },
  ]
  return (
    <section className="diag-section">
      <h2 className="diag-section-title">Expert Model Confidence</h2>
      <div className="diag-conf-header">
        <span>Expert</span><span>Confidence</span><span>%</span><span>Predicted Class</span>
      </div>
      {experts.map(({ key, label }) => {
        // models is an array from the controller; use find with flexible name matching
        // to handle 'NASA' → 'NASA/RUL' and 'Current' → 'Current Signature'
        const m = (Array.isArray(models)
          ? models.find(mod => mod.name === key || mod.name?.startsWith(key + '/') || mod.name?.startsWith(key + ' '))
          : models?.[key]) || {}
        return (
          <ConfidenceBar
            key={key}
            name={label}
            conf={m.confidence != null ? m.confidence / 100 : null}
            available={m.availability || 'standby'}
            predictedClass={m.predictedClass}
          />
        )
      })}
    </section>
  )
}

/* ── E. Live Sensor Parameters Table ─────────────────────────────────────── */
function SensorRow({ label, value, unit, status }) {
  const cls = status === 'crit' ? 'diag-row-crit' : status === 'warn' ? 'diag-row-warn' : ''
  return (
    <tr className={cls}>
      <td className="diag-td-label">{label}</td>
      <td className="diag-td-value">{value != null && !isNaN(value) ? value : '—'}</td>
      <td className="diag-td-unit">{unit}</td>
    </tr>
  )
}

function sStatus(v, warnAt, critAt) {
  if (v == null || isNaN(v)) return 'idle'
  if (v >= critAt) return 'crit'
  if (v >= warnAt) return 'warn'
  return 'ok'
}

function SensorTable({ sensors, operatingPoint }) {
  const s  = sensors || {}
  const op = operatingPoint || {}
  const stator = s.temperature?.stator
  const delta  = s.temperature?.delta
  return (
    <section className="diag-section">
      <h2 className="diag-section-title">Live Sensor Parameters</h2>
      <table className="diag-table">
        <thead>
          <tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
        </thead>
        <tbody>
          <tr className="diag-table-group"><td colSpan={3}>Mechanical</td></tr>
          <SensorRow label="Rotor Speed"   value={fmt(op.rpm, 0)}         unit="rpm" status={sStatus(op.rpm, 1550, 1600)} />
          <SensorRow label="Shaft Torque"  value={fmt(op.torque, 1)}      unit="N·m" />
          <SensorRow label="Vibration RMS" value={fmt(s.vibration?.rms, 3)} unit="g" status={sStatus(s.vibration?.rms, 0.51, 2.04)} />
          <SensorRow label="Crest Factor"  value={fmt(s.vibration?.crestFactor, 2)} unit="" />
          <SensorRow label="Kurtosis"      value={fmt(s.vibration?.kurtosis, 2)} unit="" />
          <tr className="diag-table-group"><td colSpan={3}>Electrical</td></tr>
          <SensorRow label="Phase U (Ia)"  value={fmt(s.phaseCurrent?.u, 1)} unit="A" status={sStatus(s.phaseCurrent?.u, 129, 148)} />
          <SensorRow label="Phase V (Ib)"  value={fmt(s.phaseCurrent?.v, 1)} unit="A" status={sStatus(s.phaseCurrent?.v, 129, 148)} />
          <SensorRow label="Phase W (Ic)"  value={fmt(s.phaseCurrent?.w, 1)} unit="A" status={sStatus(s.phaseCurrent?.w, 129, 148)} />
          <SensorRow label="Imbalance"     value={fmt(s.phaseCurrent?.imbalance, 2)} unit="%" />
          <tr className="diag-table-group"><td colSpan={3}>Thermal (IEC 60034-1 Class F)</td></tr>
          <SensorRow label="Stator Temp"   value={fmt(stator, 1)} unit="°C" status={sStatus(stator, 95, 120)} />
          <SensorRow label="ΔT (rise)"     value={fmt(delta, 1)}  unit="K"  status={sStatus(delta, 50, 70)} />
          <SensorRow label="Ambient Temp"  value={fmt(op.ambient, 1)} unit="°C" />
          <SensorRow label="Thermal State" value={s.thermal?.state || '—'} unit="" />
        </tbody>
      </table>
      <div className="diag-table-note">
        Vibration thresholds: ISO 10816-3 Group 2 (g). Temperature thresholds: IEC 60034-1 Class F absolute limits.
      </div>
    </section>
  )
}

/* ── F. Connection Footer ─────────────────────────────────────────────────── */
function ConnectionFooter({ connection, diagnostics }) {
  const state = connection?.state || 'unknown'
  const cls   = state === 'receiving_data' ? 'diag-conn-ok' : state.includes('reconnect') ? 'diag-conn-warn' : 'diag-conn-idle'
  return (
    <footer className="diag-footer">
      <div className={`diag-conn-pill ${cls}`}>{state.replace(/_/g, ' ')}</div>
      <div className="diag-footer-stats">
        Avg latency: {diagnostics?.avgLatencyMs != null ? `${diagnostics.avgLatencyMs} ms` : '—'}
        &nbsp;·&nbsp; P99: {diagnostics?.p99LatencyMs != null ? `${diagnostics.p99LatencyMs} ms` : '—'}
        &nbsp;·&nbsp; Clients: {diagnostics?.activeClients ?? '—'}
      </div>
    </footer>
  )
}

/* ── Root Page ────────────────────────────────────────────────────────────── */
export default function DiagnosticsPage({ controller }) {
  const { machine, sensors, operatingPoint, models, connection, diagnostics } = controller

  const healthState   = machine?.healthState    || 'UNKNOWN'
  const faultTypeName = machine?.faultTypeName  || 'Healthy'
  const explanation   = machine?.explanation    || ''
  const confidence    = machine?.predictionCertainty   // already in %
  const rulHours      = machine?.rulHours
  const modelUsed     = machine?.modelUsed      || 'Meta Fusion XGBoost'
  const lastPacket    = machine?.lastPacketText || '—'

  const healthColorKey = HEALTH_COLOR[healthState] ? healthState : 'UNKNOWN'
  const rulLabel = rulHours != null ? `${rulHours} h` : '—'
  const rulSub   = rulHours != null
    ? (rulHours < 20 ? 'Schedule replacement immediately' : rulHours < 100 ? 'Plan maintenance' : 'No immediate action required')
    : 'Awaiting NASA Bi-LSTM inference'

  return (
    <div className="diag-page">
      {/* A — Banner */}
      <StatusBanner
        healthState={healthState}
        faultTypeName={faultTypeName}
        confidence={confidence}
        lastPacketText={lastPacket}
      />

      {/* B — Metric Cards */}
      <div className="diag-cards">
        <MetricCard
          label="Health State"
          value={healthState}
          sub={`Confidence: ${confidence != null ? confidence.toFixed(1) + ' %' : '—'}`}
          color={healthColorKey.toLowerCase()}
        />
        <MetricCard
          label="Detected Fault"
          value={faultTypeName}
          sub="Categorical fault code from meta-fusion"
          color="neutral"
        />
        <MetricCard
          label="Remaining Useful Life"
          value={rulLabel}
          sub={rulSub}
          color={rulHours != null && rulHours < 20 ? 'critical' : rulHours != null && rulHours < 100 ? 'warning' : 'normal'}
        />
      </div>

      {/* C — AI Explanation */}
      <ExplanationPanel explanation={explanation} modelUsed={modelUsed} />

      {/* D — Expert Confidence */}
      <ExpertPanel models={models} />

      {/* E — Sensor Table */}
      <SensorTable sensors={sensors} operatingPoint={operatingPoint} />

      {/* F — Footer */}
      <ConnectionFooter connection={connection} diagnostics={diagnostics} />
    </div>
  )
}
