/**
 * ReportPage — Motor-Pump Field Inspection Report
 *
 * Flow:
 *   1. Operator clicks "Generate Report"
 *   2. Modal opens with 3 tabs (Job Info / Nameplate / Pre-Start)
 *   3. After completion, report renders in full (10 sections)
 *   4. Print/PDF uses @media print CSS — hides nav, only report shows
 *
 * Sections:
 *   1  Job Information
 *   2  Equipment Nameplate (Motor + Pump)
 *   3  Pre-Start Checklist
 *   4  Live Electrical Parameters
 *   5  Live Mechanical Parameters
 *   6  Live Thermal Parameters
 *   7  AI Diagnostic Result
 *   8  Maintenance Actions Performed (editable after generation)
 *   9  Active Alarms at Time of Inspection
 *   10 Sign-Off
 */
import { useState } from 'react'
import { ReportGenerateModal } from '../components/ReportGenerateModal.jsx'

/* ══════════════════════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════════════════════ */
function csvCell(v) {
  const s = String(v ?? '')
  if (s.includes(',') || s.includes('"') || s.includes('\n') || s !== s.trim())
    return `"${s.replace(/"/g, '""')}"`
  return s
}
function rowsToCsv(rows) {
  return '﻿' + rows.map((r) => r.map(csvCell).join(',')).join('\r\n')
}
function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
function statusOf(v, warnAt, critAt, invert = false) {
  if (v == null || isNaN(Number(v))) return 'idle'
  const n = Number(v)
  if (!invert) {
    if (critAt != null && n >= critAt) return 'crit'
    if (warnAt != null && n >= warnAt) return 'warn'
    return 'ok'
  } else {
    if (critAt != null && n <= critAt) return 'crit'
    if (warnAt != null && n <= warnAt) return 'warn'
    return 'ok'
  }
}
const STATUS_LABEL = { ok: 'NORMAL', warn: 'WARNING', crit: 'CRITICAL', idle: '—' }
const fmtN = (val, dp = 1) => { const n = parseFloat(val); return isNaN(n) ? '—' : n.toFixed(dp) }

function aiInterpretation(state) {
  const s = (state ?? '').toUpperCase()
  if (s === 'NORMAL')   return 'All monitored parameters are within acceptable limits. Continue normal operation and maintain the scheduled preventive maintenance programme.'
  if (s === 'WARNING')  return 'Developing degradation has been detected across one or more sensing modalities. Schedule a maintenance inspection at the earliest opportunity and increase monitoring frequency.'
  if (s === 'CRITICAL') return 'Critical parameter exceedance detected. Suspend operation, implement lockout/tagout, and notify the site engineer immediately before any restart.'
  return 'Insufficient sensor data to produce a reliable assessment. Verify system connection and sensor operation.'
}
function aiAction(state) {
  const s = (state ?? '').toUpperCase()
  if (s === 'NORMAL')   return 'Continue normal operation. No immediate corrective action required.'
  if (s === 'WARNING')  return 'Schedule maintenance inspection. Increase monitoring frequency. Do not defer beyond next planned service.'
  if (s === 'CRITICAL') return 'Stop motor immediately if safe. Lockout/tagout. Notify maintenance engineer before restart.'
  return 'Check system connection and data feed. Await diagnostic result.'
}

/* Auto report number: RPT-YYYY-NNNN */
function genReportNo() {
  const y = new Date().getFullYear()
  const n = String(Math.floor(1000 + Math.random() * 9000))
  return `RPT-${y}-${n}`
}

/* ══════════════════════════════════════════════════════════════════
   REUSABLE TABLE COMPONENTS
══════════════════════════════════════════════════════════════════ */
function StatusBadge({ cls, label }) {
  const lbl = label ?? STATUS_LABEL[cls] ?? '—'
  return <span className={`rpt-status rpt-st-${cls ?? 'idle'}`}>{lbl}</span>
}
function ParamRow({ label, value, unit, limit, status }) {
  return (
    <tr>
      <td className="rpt-td-label">{label}</td>
      <td className="rpt-td-val"><strong>{value ?? '—'}{unit ? <span className="rpt-unit"> {unit}</span> : null}</strong></td>
      <td className="rpt-td-limit">{limit}</td>
      <td className="rpt-td-status"><StatusBadge cls={status} /></td>
    </tr>
  )
}
function CheckRow({ item, req, observed, passVal }) {
  const cls = passVal === true ? 'ok' : passVal === false ? 'crit' : 'idle'
  const lbl = passVal === true ? 'PASS' : passVal === false ? 'FAIL' : '—'
  return (
    <tr>
      <td className="rpt-td-label">{item}</td>
      <td className="rpt-td-limit">{req}</td>
      <td className="rpt-td-val">{observed ?? '—'}</td>
      <td className="rpt-td-status"><StatusBadge cls={cls} label={lbl} /></td>
    </tr>
  )
}
function NameplateTable({ rows }) {
  return (
    <table className="rpt-table" style={{ width: '100%' }}>
      <tbody>
        {rows.map(([label, value]) => (
          <tr key={label}>
            <td className="rpt-td-label" style={{ width: '42%' }}>{label}</td>
            <td className="rpt-td-val"><strong>{value || '—'}</strong></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
function SectionHd({ n, children }) {
  return (
    <div className="rpt-section-hd">
      <span className="rpt-section-n">{n}</span>
      {children}
    </div>
  )
}
function SubHd({ children, style }) {
  return <div className="rpt-sub-hd" style={style}>{children}</div>
}
function ParamTable({ children, cols = ['Parameter', 'Reading', 'Rated / Limit', 'Status'] }) {
  return (
    <table className="rpt-table rpt-table-full">
      <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>{children}</tbody>
    </table>
  )
}

/* ══════════════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════════════ */
export function ReportPage({ controller }) {
  const now     = new Date()
  const ts      = now.toLocaleString([], { dateStyle: 'full', timeStyle: 'short' })
  const fileTs  = now.toISOString().replace(/[:.]/g, '-').slice(0, 19)

  const { machine, sensors, alarms, operatingPoint, session, recommendation } = controller

  /* ── Report generation state ── */
  const [reportGenerated, setReportGenerated] = useState(false)
  const [showModal,       setShowModal]       = useState(false)
  const [reportNo,        setReportNo]        = useState('')
  const [reportData,      setReportData]      = useState(null) // { job, motor, pump, pre }

  /* ── Post-generation editable fields (Section 8) ── */
  const [workCarriedOut, setWorkCarriedOut] = useState('')
  const [partsRows, setPartsRows] = useState([
    { part: '', partNo: '', qty: '', supplier: '' },
  ])
  const [nextMaintType, setNextMaintType] = useState('Routine')
  const [nextMaintDate, setNextMaintDate] = useState('')
  const [supervisorName, setSupervisorName] = useState('')
  const [nextInspDate,   setNextInspDate]   = useState('')
  const [designation,    setDesignation]    = useState(() => {
    // Pre-fill from session role, capitalised — inspector can override with actual job title
    const role = session?.role || ''
    return role.charAt(0).toUpperCase() + role.slice(1)
  })

  const handleGenerate = (data) => {
    setReportData(data)
    setReportNo(genReportNo())
    setReportGenerated(true)
    setShowModal(false)
  }

  /* ── Live data ── */
  const healthState = machine?.healthState ?? 'UNKNOWN'
  const healthCls   = { NORMAL: 'ok', WARNING: 'warn', CRITICAL: 'crit' }[healthState.toUpperCase()] ?? 'idle'
  const cert        = parseFloat(machine?.predictionCertainty)
  const certStr     = !isNaN(cert) ? `${cert.toFixed(0)}%` : '—'
  const rulHours    = parseFloat(machine?.rulHours)
  const rulCls      = isNaN(rulHours) ? 'idle' : rulHours < 50 ? 'crit' : rulHours < 150 ? 'warn' : 'ok'
  const rulDays     = !isNaN(rulHours) ? `(≈ ${(rulHours / 8).toFixed(0)} working days)` : ''
  const faultCount  = alarms?.active?.length ?? 0
  const imb         = parseFloat(sensors?.phaseCurrent?.imbalance)
  const imbCls      = isNaN(imb) ? 'idle' : imb > 12 ? 'crit' : imb > 8 ? 'warn' : 'ok'
  const sOf = statusOf

  /* ── Landing page (before generation) ── */
  if (!reportGenerated) {
    return (
      <div className="rpt-shell">
        {showModal && (
          <ReportGenerateModal
            session={session}
            onGenerate={handleGenerate}
            onClose={() => setShowModal(false)}
          />
        )}
        <div className="rpt-landing">
          <div className="rpt-landing-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent)' }}>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div className="page-title" style={{ marginTop: 16 }}>Motor-Pump Field Inspection Report</div>
          <div className="page-sub" style={{ marginTop: 6, maxWidth: 480, textAlign: 'center' }}>
            Complete the inspection form to generate a standards-compliant field report.
            The report will include all live AI diagnostic results, sensor readings,
            and your entered site information.
          </div>

          {/* Live status summary */}
          <div className="rpt-landing-status">
            <div className="rpt-landing-stat">
              <div className="rpt-landing-stat-label">Current Health</div>
              <span className={`rpt-health-badge rpt-health-${healthCls}`}>
                {healthCls === 'ok' ? '● NORMAL' : healthCls === 'warn' ? '▲ WARNING' : healthCls === 'crit' ? '■ CRITICAL' : '○ UNKNOWN'}
              </span>
            </div>
            <div className="rpt-landing-stat">
              <div className="rpt-landing-stat-label">RUL</div>
              <div className={`rpt-landing-stat-val rpt-rul-${rulCls}`}>
                {!isNaN(rulHours) ? `${rulHours.toFixed(0)} h` : '—'}
              </div>
            </div>
            <div className="rpt-landing-stat">
              <div className="rpt-landing-stat-label">Prediction Certainty</div>
              <div className="rpt-landing-stat-val">{certStr}</div>
            </div>
            <div className="rpt-landing-stat">
              <div className="rpt-landing-stat-label">Active Alarms</div>
              <div className={`rpt-landing-stat-val ${faultCount > 0 ? 'rpt-summary-crit' : 'rpt-summary-ok'}`}>
                {faultCount > 0 ? `${faultCount} ACTIVE` : '0 — Clear'}
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary rpt-generate-btn"
            onClick={() => setShowModal(true)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Generate Report
          </button>
          <div style={{ fontSize: 12, color: 'var(--txt-3)', marginTop: 12 }}>
            You will fill in job information, motor nameplate data, and pre-start checklist.
          </div>
        </div>
      </div>
    )
  }

  /* ── Destructure report form data ── */
  const { job, motor, pump, pre } = reportData

  /* Pre-start pass/fail helpers */
  const vPass  = (k, min, max) => { const n = parseFloat(pre[k]); return isNaN(n) ? null : n >= min && n <= max }
  const okPre  = (k) => pre[k] ? pre[k].toUpperCase() === 'OK' || pre[k] === 'Yes' : null

  /* ══════════════════════════════════════════════════════════════════
     GENERATED REPORT
  ══════════════════════════════════════════════════════════════════ */
  return (
    <div className="rpt-shell">
      {showModal && (
        <ReportGenerateModal
          session={session}
          onGenerate={handleGenerate}
          onClose={() => setShowModal(false)}
        />
      )}

      {/* ── Screen toolbar (hidden when printing) ── */}
      <div className="rpt-toolbar no-print">
        <div>
          <div className="page-title">Field Inspection Report</div>
          <div className="page-sub">{reportNo} &nbsp;·&nbsp; Generated {ts}</div>
        </div>
        <div className="rpt-export-row">
          <button className="btn btn-ghost rpt-btn" onClick={() => {
            setReportGenerated(false)
            setShowModal(true)
          }}>
            ✎ Edit / Regenerate
          </button>
          <button className="btn btn-primary rpt-btn" onClick={() => window.print()}>
            <RptPrintIcon /> Print / Save PDF
          </button>
          <button className="btn btn-ghost rpt-btn" onClick={() =>
            downloadBlob(
              JSON.stringify({ reportNo, generatedAt: now.toISOString(), job, motor, pump, pre, machine, operatingPoint, sensors, alarms, recommendation }, null, 2),
              `field-report-${fileTs}.json`, 'application/json')}>
            <RptJsonIcon /> Export JSON
          </button>
        </div>
      </div>

      {/* ══ A4 DOCUMENT ══ */}
      <div className="rpt-doc">

        {/* ── HEADER ── */}
        <div className="rpt-cover">
          <div className="rpt-cover-brand">
            <div className="rpt-cover-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4M12 18v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M2 12h4M18 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
              </svg>
            </div>
            <div>
              <div className="rpt-cover-name">MOTOR-PUMP FIELD INSPECTION REPORT</div>
              <div className="rpt-cover-sub">MotorGuard Digital Twin — Predictive Maintenance System v2.1</div>
            </div>
          </div>
          <div className="rpt-cover-meta">
            <div className="rpt-cover-row"><span>Report No.</span><strong>{reportNo}</strong></div>
            <div className="rpt-cover-row"><span>Date &amp; Time</span><strong>{ts}</strong></div>
            <div className="rpt-cover-row"><span>Machine ID</span><strong>{machine?.machineId ?? 'SCIM-01'}</strong></div>
            <div className="rpt-cover-row"><span>Inspector</span><strong>{job.operatorName || '—'}</strong></div>
            <div className="rpt-cover-row"><span>Site</span><strong>{job.site || '—'}</strong></div>
            <div className="rpt-cover-row"><span>Work Order</span><strong>{job.workOrder || '—'}</strong></div>
          </div>
        </div>

        {/* ══ SECTION 1 — JOB INFORMATION ══ */}
        <div className="rpt-section">
          <SectionHd n="1">Job Information</SectionHd>
          <table className="rpt-table rpt-table-full">
            <tbody>
              <tr><td className="rpt-td-label">Work Order / PM Ticket</td><td className="rpt-td-val"><strong>{job.workOrder || '—'}</strong></td>
                  <td className="rpt-td-label">Inspection Type</td><td className="rpt-td-val"><strong>{job.inspType}</strong></td></tr>
              <tr><td className="rpt-td-label">Site / Location</td><td className="rpt-td-val"><strong>{job.site || '—'}</strong></td>
                  <td className="rpt-td-label">Date of Inspection</td><td className="rpt-td-val"><strong>{job.date}</strong></td></tr>
              <tr><td className="rpt-td-label">Shift</td><td className="rpt-td-val"><strong>{job.shift}{job.shiftTime ? ` — starts ${job.shiftTime}` : ''}</strong></td>
                  <td className="rpt-td-label">Department / Team</td><td className="rpt-td-val"><strong>{job.department || '—'}</strong></td></tr>
              <tr><td className="rpt-td-label">Inspector Name</td><td className="rpt-td-val"><strong>{job.operatorName || '—'}</strong></td>
                  <td className="rpt-td-label">Contact No.</td><td className="rpt-td-val"><strong>{job.contact || '—'}</strong></td></tr>
            </tbody>
          </table>
        </div>

        {/* ══ SECTION 2 — EQUIPMENT NAMEPLATE ══ */}
        <div className="rpt-section">
          <SectionHd n="2">Equipment Nameplate Data</SectionHd>
          <div className="rpt-nameplate-grid">
            <div>
              <SubHd>Motor</SubHd>
              <NameplateTable rows={[
                ['Manufacturer',     motor.manufacturer],
                ['Model / Type',     motor.model || 'Squirrel-Cage Induction Motor (SCIM)'],
                ['Serial No.',       motor.serialNo],
                ['Frame Size (IEC)', motor.frameSize],
                ['Rated Power',      motor.ratedPower],
                ['Voltage / Supply', motor.voltage],
                ['Rated Current',    motor.ratedCurrent],
                ['Rated Speed',      motor.ratedSpeed],
                ['Efficiency Class', motor.effClass],
                ['Insulation Class', motor.insulation],
                ['Duty Cycle',       motor.dutyCycle],
                ['Thermal Protect.', motor.thermalProt],
                ['Enclosure (IP)',   motor.enclosure],
                ['Mounting',         motor.mounting],
                ['Installation Date',motor.installedDate],
                ['Operating Hours',  motor.operatingHours ? `${motor.operatingHours} h` : ''],
                ['Rewound',          motor.rewound === 'Yes' ? `Yes — ${motor.rewoundDate || ''}` : 'No'],
              ]} />
            </div>
            <div>
              <SubHd>Pump</SubHd>
              <NameplateTable rows={[
                ['Manufacturer',    pump.manufacturer],
                ['Model / Type',    pump.model || 'End-Suction Centrifugal Pump'],
                ['Serial No.',      pump.serialNo],
                ['Flow Rate',       pump.flowRate],
                ['Total Head',      pump.head],
                ['Rated Speed',     pump.ratedSpeed],
                ['Impeller Dia.',   pump.impellerDia],
                ['Seal Type',       pump.sealType],
                ['Orientation',     pump.orientation],
                ['Installation Date', pump.installedDate],
              ]} />
            </div>
          </div>
        </div>

        {/* ══ SECTION 3 — PRE-START CHECKLIST ══ */}
        <div className="rpt-section">
          <SectionHd n="3">Pre-Start &amp; Startup Checklist</SectionHd>
          <p className="rpt-section-note">Completed before motor start. Values entered by inspector on site.</p>
          <table className="rpt-table rpt-table-full">
            <thead><tr><th>Item</th><th>Requirement</th><th>Observed Value</th><th>Status</th></tr></thead>
            <tbody>
              <CheckRow item="Supply Voltage L1–L2" req="400 V ±10% (360–440 V)" observed={pre.vL1L2 ? `${pre.vL1L2} V` : '—'} passVal={vPass('vL1L2', 360, 440)} />
              <CheckRow item="Supply Voltage L2–L3" req="400 V ±10% (360–440 V)" observed={pre.vL2L3 ? `${pre.vL2L3} V` : '—'} passVal={vPass('vL2L3', 360, 440)} />
              <CheckRow item="Supply Voltage L1–L3" req="400 V ±10% (360–440 V)" observed={pre.vL1L3 ? `${pre.vL1L3} V` : '—'} passVal={vPass('vL1L3', 360, 440)} />
              <CheckRow item="Supply Frequency"      req="50 Hz ±2% (49–51 Hz)"   observed={pre.freq  ? `${pre.freq} Hz` : '—'} passVal={vPass('freq', 49, 51)} />
              <CheckRow item="Insulation Resistance (Megger)" req="≥1 MΩ at 500 V DC" observed={pre.insulRes ? `${pre.insulRes} MΩ` : '—'} passVal={pre.insulRes ? parseFloat(pre.insulRes) >= 1 : null} />
              <CheckRow item="Earth Continuity"     req="<1 Ω" observed={pre.earthCont ? `${pre.earthCont} Ω` : '—'} passVal={pre.earthCont ? parseFloat(pre.earthCont) < 1 : null} />
              <CheckRow item="Bearing Lubrication"  req="Per manufacturer spec"      observed={pre.lubrication}   passVal={okPre('lubrication')} />
              <CheckRow item="Cooling / Ventilation" req="Clear, unobstructed, operational" observed={pre.cooling} passVal={okPre('cooling')} />
              <CheckRow item="Guards &amp; Safety Covers" req="All in place and secure" observed={pre.guards}    passVal={okPre('guards')} />
              <CheckRow item="Coupling Alignment"   req="Within manufacturer tolerance" observed={pre.coupling}  passVal={okPre('coupling')} />
              <CheckRow item="Motor Cleanliness"    req="Free from dust / oil accumulation" observed={pre.cleanliness} passVal={okPre('cleanliness')} />
              <CheckRow item="Mounting Bolts Torqued" req="Per torque spec"            observed={pre.boltsTorque}  passVal={okPre('boltsTorque')} />
            </tbody>
          </table>
        </div>

        {/* ══ SECTION 4 — ELECTRICAL PARAMETERS ══ */}
        <div className="rpt-section">
          <SectionHd n="4">Live Electrical Parameters — Running Condition</SectionHd>

          <SubHd>4.1 — Three-Phase Supply</SubHd>
          <ParamTable>
            <ParamRow label="Supply Voltage"    value={fmtN(sensors?.supplyParams?.voltage,    1)} unit="V"   limit="Rated: 400 V  |  360–440 V range" status={sOf(sensors?.supplyParams?.voltage, null, null)} />
            <ParamRow label="Supply Frequency"  value={fmtN(sensors?.supplyParams?.frequency,  2)} unit="Hz"  limit="Rated: 50 Hz  |  49–51 Hz range"  status={sOf(sensors?.supplyParams?.frequency, null, null)} />
            <ParamRow label="Power Factor"      value={fmtN(sensors?.supplyParams?.powerFactor,3)} unit=""    limit="Min: 0.85 (lagging)"               status="idle" />
            <ParamRow label="Active Power"      value={fmtN(sensors?.supplyParams?.activePower,2)} unit="kW"  limit="Rated: 15 kW"                      status={sOf(sensors?.supplyParams?.activePower, 14, 17)} />
            <ParamRow label="Apparent Power"    value={fmtN(sensors?.supplyParams?.apparentPower,2)} unit="kVA" limit=""                               status="idle" />
            <ParamRow label="THD — Current"     value={fmtN(sensors?.supplyParams?.thdCurrent, 1)} unit="%"   limit="IEC 61000-3-2  |  Limit: &lt;5%"  status={sOf(sensors?.supplyParams?.thdCurrent, 3, 5)} />
          </ParamTable>

          <SubHd style={{ marginTop: 16 }}>4.2 — Stator Phase Currents (IEC 60034-1)</SubHd>
          <table className="rpt-table rpt-table-full">
            <thead><tr><th>Phase</th><th>Current (A)</th><th>Rated (A)</th><th>Deviation from Mean</th><th>Status</th></tr></thead>
            <tbody>
              {[
                { ph: 'L1 (U)', val: sensors?.phaseCurrent?.u },
                { ph: 'L2 (V)', val: sensors?.phaseCurrent?.v },
                { ph: 'L3 (W)', val: sensors?.phaseCurrent?.w },
              ].map(({ ph, val }) => {
                const n = parseFloat(val)
                const u = parseFloat(sensors?.phaseCurrent?.u), v2 = parseFloat(sensors?.phaseCurrent?.v), w = parseFloat(sensors?.phaseCurrent?.w)
                const mean = (!isNaN(u) && !isNaN(v2) && !isNaN(w)) ? (u + v2 + w) / 3 : null
                const dev  = mean != null && !isNaN(n) ? `${((n - mean) / mean * 100).toFixed(1)} %` : '—'
                return (
                  <tr key={ph}>
                    <td className="rpt-td-label"><strong>{ph}</strong></td>
                    <td className="rpt-td-val"><strong>{!isNaN(n) ? n.toFixed(2) : '—'}</strong></td>
                    <td className="rpt-td-limit">30 A</td>
                    <td className="rpt-td-val">{dev}</td>
                    <td className="rpt-td-status"><StatusBadge cls={sOf(val, 28, 35)} /></td>
                  </tr>
                )
              })}
              <tr style={{ borderTop: '2px solid #e2e8f0' }}>
                <td className="rpt-td-label"><strong>Phase Imbalance</strong></td>
                <td className="rpt-td-val" colSpan={2}><strong>{!isNaN(imb) ? imb.toFixed(1) : '—'} %</strong></td>
                <td className="rpt-td-limit">Warning: &gt;8%  |  Critical: &gt;12%</td>
                <td className="rpt-td-status"><StatusBadge cls={imbCls} /></td>
              </tr>
            </tbody>
          </table>
          <p className="rpt-table-note">NEMA MG-1 / IEC 60034-26: Sustained phase imbalance &gt;1% causes additional rotor heating. Values &gt;5% risk premature failure.</p>
        </div>

        {/* ══ SECTION 5 — MECHANICAL PARAMETERS ══ */}
        <div className="rpt-section">
          <SectionHd n="5">Live Mechanical Parameters — Running Condition</SectionHd>
          <SubHd>5.1 — Speed &amp; Load</SubHd>
          <ParamTable>
            <ParamRow label="Rotor Speed"   value={fmtN(operatingPoint?.rpm,    0)} unit="RPM" limit="Rated: 1480  |  Warn: &gt;1520  |  Crit: &gt;1550" status={sOf(operatingPoint?.rpm, 1520, 1550)} />
            <ParamRow label="Shaft Torque"  value={fmtN(operatingPoint?.torque, 1)} unit="N·m" limit="Rated: 97.3 N·m  |  Warn: &gt;90  |  Crit: &gt;110" status={sOf(operatingPoint?.torque, 90, 110)} />
            <ParamRow label="Load Factor"   value={fmtN(operatingPoint?.loadFactor, 1)} unit="%" limit="Normal: ≤100%  |  Warn: &gt;90%" status={sOf(operatingPoint?.loadFactor, 90, 100)} />
          </ParamTable>
          <SubHd style={{ marginTop: 16 }}>5.2 — Vibration (ISO 10816-3)</SubHd>
          <ParamTable>
            <ParamRow label="Vibration RMS"    value={fmtN(sensors?.vibration?.rms,         3)} unit="g"  limit="Zone A: &lt;2.3 g  |  Zone C: &lt;7.1 g  |  Crit: ≥8.0 g" status={sOf(sensors?.vibration?.rms, 5, 8)} />
            <ParamRow label="Vibration Kurtosis" value={fmtN(sensors?.vibration?.kurtosis,  2)} unit=""   limit="Normal: &lt;4  |  Warn: ≥10  |  Crit: ≥16"                  status={sOf(sensors?.vibration?.kurtosis, 10, 16)} />
            <ParamRow label="Crest Factor"     value={fmtN(sensors?.vibration?.crestFactor, 2)} unit=""   limit="Normal: &lt;4  |  Warn: ≥6  |  Crit: ≥8"                     status={sOf(sensors?.vibration?.crestFactor, 6, 8)} />
          </ParamTable>
          <p className="rpt-table-note">ISO 10816-3: Zone A=new machines  |  Zone B=acceptable long-term  |  Zone C=alarm, investigate  |  Zone D=danger, stop machine.</p>
        </div>

        {/* ══ SECTION 6 — THERMAL PARAMETERS ══ */}
        <div className="rpt-section rpt-section-break-after">
          <SectionHd n="6">Live Thermal Parameters (IEC 60034-1)</SectionHd>
          <ParamTable>
            <ParamRow label="Stator Winding Temp."   value={fmtN(sensors?.temperature?.stator,  1)} unit="°C" limit="Warn: 65 °C  |  Crit: 85 °C  |  Class F abs. limit: 155 °C" status={sOf(sensors?.temperature?.stator,  65, 85)} />
            <ParamRow label="Bearing Temp. (DE)"     value={fmtN(sensors?.temperature?.bearing, 1)} unit="°C" limit="Warn: 70 °C  |  Crit: 85 °C"                                  status={sOf(sensors?.temperature?.bearing, 70, 85)} />
            <ParamRow label="Ambient Temperature"    value={fmtN(operatingPoint?.ambient,        1)} unit="°C" limit="Max: 40 °C (IEC 60034-1 standard rating)"                     status={sOf(operatingPoint?.ambient, 35, 40)} />
            <ParamRow label="Temperature Rise (ΔT)"  value={fmtN(sensors?.temperature?.delta,   1)} unit="K"  limit="Warn: 20 K  |  Crit: 30 K (Stator − Ambient)"                 status={sOf(sensors?.temperature?.delta,   20, 30)} />
            <ParamRow label="Thermal Hotspot (IR)"   value={fmtN(sensors?.thermal?.hotSpot,      1)} unit="°C" limit="Warn: 80 °C  |  Crit: 95 °C"                                  status={sOf(sensors?.thermal?.hotSpot,     80, 95)} />
          </ParamTable>
          <p className="rpt-table-note">IEC 60034-1: Each 10 °C above rated temperature halves insulation life (Arrhenius rule). Maintain adequate ventilation at all times.</p>
        </div>

        {/* ══ SECTION 7 — AI DIAGNOSTIC RESULT ══ */}
        <div className="rpt-section rpt-avoid-break">
          <SectionHd n="7">AI Predictive Diagnostic Result</SectionHd>
          <p className="rpt-section-note">
            Model: Meta-Fusion (CWRU-CNN + Induction-CNN + NASA Bi-LSTM-Attn + Current-CNN + Thermal-MobileNetV2)
            &nbsp;·&nbsp; System accuracy: 90.67 %  &nbsp;·&nbsp; F1 macro: 0.906
          </p>

          <div className="rpt-ai-result-grid">
            <div className="rpt-ai-cell rpt-ai-cell-wide">
              <div className="rpt-ai-cell-label">Health Classification</div>
              <span className={`rpt-health-badge rpt-health-${healthCls}`} style={{ fontSize: 16 }}>
                {healthCls === 'ok' ? '● NORMAL' : healthCls === 'warn' ? '▲ WARNING' : healthCls === 'crit' ? '■ CRITICAL' : '○ UNKNOWN'}
              </span>
            </div>
            <div className="rpt-ai-cell">
              <div className="rpt-ai-cell-label">Remaining Useful Life</div>
              <div className={`rpt-ai-cell-val rpt-rul-val-${rulCls}`}>
                {!isNaN(rulHours) ? rulHours.toFixed(0) : '—'}
                <span className="rpt-ai-cell-unit">h</span>
              </div>
              <div className="rpt-ai-cell-sub">{rulDays}</div>
            </div>
            <div className="rpt-ai-cell">
              <div className="rpt-ai-cell-label">Prediction Certainty</div>
              <div className="rpt-ai-cell-val">{certStr}</div>
              <div className="rpt-ai-cell-sub">Per this inference</div>
            </div>
            <div className="rpt-ai-cell">
              <div className="rpt-ai-cell-label">Model Accuracy</div>
              <div className="rpt-ai-cell-val">90.67 %</div>
              <div className="rpt-ai-cell-sub">F1 = 0.906</div>
            </div>
          </div>

          {/* RUL bar */}
          {!isNaN(rulHours) && (
            <div className="rpt-rul-bar-wrap" style={{ marginTop: 12 }}>
              <div className="rpt-rul-bar">
                <div className={`rpt-rul-bar-fill rpt-rul-${rulCls}`}
                  style={{ width: `${Math.min(100, Math.max(2, (rulHours / 500) * 100))}%` }} />
              </div>
              <div className="rpt-rul-bar-labels">
                <span style={{ color: '#b91c1c' }}>0 h — Critical</span>
                <span style={{ color: '#b45309' }}>150 h — Warning</span>
                <span style={{ color: '#15803d' }}>500 h — Full life</span>
              </div>
            </div>
          )}

          <table className="rpt-table rpt-table-full" style={{ marginTop: 14 }}>
            <tbody>
              <tr>
                <td className="rpt-td-label" style={{ width: '22%' }}>Fault Status</td>
                <td colSpan={2}><StatusBadge cls={healthCls} label={healthState.toUpperCase()} /></td>
              </tr>
              <tr>
                <td className="rpt-td-label">Interpretation</td>
                <td colSpan={2} className="rpt-td-val" style={{ fontStyle: 'italic', lineHeight: 1.6 }}>
                  {aiInterpretation(healthState)}
                </td>
              </tr>
              <tr>
                <td className="rpt-td-label">Required Action</td>
                <td colSpan={2} className="rpt-td-val" style={{ fontWeight: 700, lineHeight: 1.6, color: healthCls === 'crit' ? '#b91c1c' : healthCls === 'warn' ? '#b45309' : '#15803d' }}>
                  {aiAction(healthState)}
                </td>
              </tr>
            </tbody>
          </table>
          <p className="rpt-table-note">
            AI results are based on sensor data from MATLAB/Simulink via MotorGuard Digital Twin v2.1.
            Always verify AI results against physical inspection before acting. For field use only.
          </p>
        </div>

        {/* ══ SECTION 8 — MAINTENANCE ACTIONS PERFORMED ══ */}
        <div className="rpt-section rpt-section-break-after">
          <SectionHd n="8">Maintenance Actions Performed</SectionHd>

          <div className="rpt-work-area">
            <label className="rpt-modal-label">Work Carried Out (describe all actions taken)</label>
            <textarea
              className="rpt-work-textarea no-print"
              value={workCarriedOut}
              onChange={(e) => setWorkCarriedOut(e.target.value)}
              placeholder="Describe maintenance actions performed, findings, and any observations…"
              rows={5}
            />
            <div className="print-only rpt-work-print">{workCarriedOut || '(No entries)'}</div>
          </div>

          <SubHd style={{ marginTop: 16 }}>Parts / Materials Replaced</SubHd>
          <table className="rpt-table rpt-table-full no-print">
            <thead><tr><th>Part / Component</th><th>Part Number</th><th>Quantity</th><th>Supplier / Source</th><th></th></tr></thead>
            <tbody>
              {partsRows.map((r, i) => (
                <tr key={i}>
                  <td><input className="rpt-edit-input" value={r.part}     onChange={(e) => { const next = [...partsRows]; next[i] = { ...r, part:     e.target.value }; setPartsRows(next) }} placeholder="e.g. Bearing 6205-2RS" /></td>
                  <td><input className="rpt-edit-input" value={r.partNo}   onChange={(e) => { const next = [...partsRows]; next[i] = { ...r, partNo:   e.target.value }; setPartsRows(next) }} placeholder="Part no." /></td>
                  <td><input className="rpt-edit-input" value={r.qty}      onChange={(e) => { const next = [...partsRows]; next[i] = { ...r, qty:      e.target.value }; setPartsRows(next) }} placeholder="1" /></td>
                  <td><input className="rpt-edit-input" value={r.supplier} onChange={(e) => { const next = [...partsRows]; next[i] = { ...r, supplier: e.target.value }; setPartsRows(next) }} placeholder="Supplier" /></td>
                  <td><button className="btn btn-ghost" style={{ fontSize: 11, padding: '2px 8px' }} onClick={() => setPartsRows((p) => p.filter((_, j) => j !== i))}>✕</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className="btn btn-ghost no-print" style={{ fontSize: 12, marginTop: 6 }}
            onClick={() => setPartsRows((p) => [...p, { part: '', partNo: '', qty: '', supplier: '' }])}>
            + Add row
          </button>
          {/* Print version of parts */}
          <table className="rpt-table rpt-table-full print-only" style={{ marginTop: 8 }}>
            <thead><tr><th>Part / Component</th><th>Part Number</th><th>Quantity</th><th>Supplier</th></tr></thead>
            <tbody>
              {partsRows.filter((r) => r.part).map((r, i) => (
                <tr key={i}><td>{r.part}</td><td>{r.partNo}</td><td>{r.qty}</td><td>{r.supplier}</td></tr>
              ))}
              {partsRows.filter((r) => r.part).length === 0 && (
                <tr><td colSpan={4} style={{ fontStyle: 'italic' }}>No parts replaced</td></tr>
              )}
            </tbody>
          </table>

          <SubHd style={{ marginTop: 16 }}>Next Maintenance</SubHd>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="rpt-modal-field" style={{ flex: 1, minWidth: 180 }}>
              <label className="rpt-modal-label">Type</label>
              <select className="rpt-modal-input" value={nextMaintType} onChange={(e) => setNextMaintType(e.target.value)}>
                {['Routine', 'Predictive', 'Corrective', 'Emergency'].map((o) => <option key={o}>{o}</option>)}
              </select>
            </div>
            <div className="rpt-modal-field" style={{ flex: 1, minWidth: 180 }}>
              <label className="rpt-modal-label">Due Date</label>
              <input className="rpt-modal-input" value={nextMaintDate} onChange={(e) => setNextMaintDate(e.target.value)} placeholder="DD/MM/YYYY" pattern="\d{2}/\d{2}/\d{4}" title="Format: DD/MM/YYYY (e.g. 23/05/2026)" />
            </div>
          </div>
        </div>

        {/* ══ SECTION 9 — ACTIVE ALARMS ══ */}
        <div className="rpt-section">
          <SectionHd n="9">Active Alarms at Time of Inspection</SectionHd>
          {faultCount === 0 ? (
            <p className="rpt-no-faults">✓ No active faults at time of report generation.</p>
          ) : (
            <table className="rpt-table rpt-table-full">
              <thead><tr><th>Severity</th><th>Description</th><th>Source</th><th>Time Raised</th><th>Ack.</th><th>Required Action</th></tr></thead>
              <tbody>
                {(alarms?.active ?? []).map((a, i) => (
                  <tr key={i}>
                    <td><StatusBadge cls={{ critical: 'crit', warning: 'warn' }[a.severity?.toLowerCase()] ?? 'ok'} label={a.severity?.toUpperCase()} /></td>
                    <td>{a.message ?? '—'}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{a.source ?? '—'}</td>
                    <td style={{ whiteSpace: 'nowrap', fontSize: 11 }}>{a.raisedAt ?? '—'}</td>
                    <td>{a.acknowledged ? 'Yes' : 'No'}</td>
                    <td style={{ fontSize: 11, fontStyle: 'italic' }}>
                      {a.severity?.toLowerCase() === 'critical' ? 'Notify engineer — isolate machine' : 'Investigate within 10 min'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ══ SECTION 10 — SIGN-OFF ══ */}
        <div className="rpt-section rpt-avoid-break">
          <SectionHd n="10">Inspection Record &amp; Sign-Off</SectionHd>
          <div className="rpt-signoff-grid">
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Inspector Name</div>
              <div className="rpt-signoff-line">{job.operatorName || '_______________________'}</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Designation / Role</div>
              <input className="rpt-signoff-input no-print" value={designation}
                onChange={(e) => setDesignation(e.target.value)} placeholder="e.g. Maintenance Engineer" />
              <div className="rpt-signoff-line print-only">{designation || '_______________________'}</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Inspector Signature</div>
              <div className="rpt-signoff-line">_______________________</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Date of Inspection</div>
              <div className="rpt-signoff-line">{job.date}</div>
            </div>

            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Supervisor Name</div>
              <input className="rpt-signoff-input no-print" value={supervisorName}
                onChange={(e) => setSupervisorName(e.target.value)} placeholder="Supervisor / approver name" />
              <div className="rpt-signoff-line print-only">{supervisorName || '_______________________'}</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Supervisor Signature</div>
              <div className="rpt-signoff-line">_______________________</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Supervisor Date</div>
              <div className="rpt-signoff-line">_______________________</div>
            </div>
            <div className="rpt-signoff-block">
              <div className="rpt-signoff-label">Next Inspection Due</div>
              <input className="rpt-signoff-input no-print" value={nextInspDate}
                onChange={(e) => setNextInspDate(e.target.value)} placeholder="DD/MM/YYYY"
                pattern="\d{2}/\d{2}/\d{4}" title="Format: DD/MM/YYYY (e.g. 23/05/2026)" />
              <div className="rpt-signoff-line print-only">{nextInspDate || '_______________________'}</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="rpt-footer">
          <span>Generated by MotorGuard Digital Twin v2.1 &nbsp;·&nbsp; {reportNo} &nbsp;·&nbsp; {ts}</span>
          <span>For field use only. Verify all AI results against physical inspection before acting.</span>
        </div>

      </div>{/* end rpt-doc */}
    </div>
  )
}

/* Toolbar icons */
function RptPrintIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
}
function RptJsonIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
}
