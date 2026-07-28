/**
 * ReportGenerateModal
 * Three-tab modal collecting operator, nameplate, and pre-start information
 * before the field inspection report is generated.
 *
 * Tabs:
 *  1. Job Information    — work order, site, shift, operator
 *  2. Equipment Nameplate — motor + pump IEC nameplate fields
 *  3. Pre-Start Checklist — voltages, insulation, physical checks
 */
import { useState } from 'react'

/* ── Mini form-field helpers ── */
function Field({ label, required, children }) {
  return (
    <div className="rpt-modal-field">
      <label className="rpt-modal-label">
        {label}{required && <span className="rpt-modal-req" aria-label="required"> *</span>}
      </label>
      {children}
    </div>
  )
}

function Input({ value, onChange, placeholder, type = 'text' }) {
  return (
    <input
      className="rpt-modal-input"
      type={type}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder ?? ''}
    />
  )
}

function Select({ value, onChange, options }) {
  return (
    <select className="rpt-modal-input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => (
        <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
      ))}
    </select>
  )
}

const TABS = ['Job Information', 'Equipment Nameplate', 'Pre-Start Checklist']

export function ReportGenerateModal({ session, onGenerate, onClose }) {
  const [activeTab, setActiveTab] = useState(0)

  /* Tab 1 — Job Information */
  const [job, setJob] = useState({
    workOrder:    '',
    site:         '',
    inspType:     'Routine',
    shift:        'Day',
    shiftTime:    '',
    operatorName: session?.displayName || session?.username || '',
    contact:      '',
    department:   '',
    date:         new Date().toLocaleDateString('en-GB'),
  })
  const setJ = (k) => (v) => setJob((p) => ({ ...p, [k]: v }))

  /* Tab 2 — Equipment Nameplate */
  const [motor, setMotor] = useState({
    manufacturer:  '',
    model:         '',
    serialNo:      '',
    frameSize:     '',
    ratedPower:    '75 kW',
    voltage:       '400 V / 3Ø / 50 Hz',
    ratedCurrent:  '129 A (line) / 74.5 A (phase)',
    ratedSpeed:    '1480 RPM',
    effClass:      'IE3',
    insulation:    'Class F',
    dutyCycle:     'S1',
    enclosure:     'IP55 / TEFC',
    mounting:      'B3 (Foot)',
    installedDate: '',
    operatingHours:'',
    rewound:       'No',
    rewoundDate:   '',
  })
  const setM = (k) => (v) => setMotor((p) => ({ ...p, [k]: v }))

  const [pump, setPump] = useState({
    manufacturer:  '',
    model:         '',
    serialNo:      '',
    flowRate:      '45 m³/h',
    head:          '32 m',
    ratedSpeed:    '1480 RPM',
    impellerDia:   '210 mm',
    sealType:      'Mechanical seal',
    orientation:   'Horizontal',
    installedDate: '',
  })
  const setP = (k) => (v) => setPump((p) => ({ ...p, [k]: v }))

  /* Tab 3 — Pre-Start Checklist */
  const [pre, setPre] = useState({
    vL1L2:       '',
    vL2L3:       '',
    vL1L3:       '',
    freq:        '',
    insulRes:    '',
    earthCont:   '',
    lubrication: 'OK',
    cooling:     'OK',
    guards:      'OK',
    coupling:    'OK',
    cleanliness: 'OK',
    boltsTorque: 'Yes',
  })
  const setPK = (k) => (v) => setPre((p) => ({ ...p, [k]: v }))

  /* Validation: Tab 1 requires workOrder and site */
  const tab1Valid = job.workOrder.trim().length > 0 && job.site.trim().length > 0
  const allValid  = tab1Valid

  const handleGenerate = () => {
    if (!allValid) return
    onGenerate({ job, motor, pump, pre })
  }

  return (
    <div className="rpt-modal-overlay" role="dialog" aria-modal="true" aria-label="Generate Report">
      <div className="rpt-modal-panel">

        {/* Header */}
        <div className="rpt-modal-header">
          <div>
            <div className="rpt-modal-title">Generate Field Inspection Report</div>
            <div className="rpt-modal-sub">Complete all required fields (*) before generating</div>
          </div>
          <button className="rpt-modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Tab strip */}
        <div className="rpt-modal-tabs">
          {TABS.map((t, i) => (
            <button
              key={i}
              className={`rpt-modal-tab${activeTab === i ? ' active' : ''}`}
              onClick={() => setActiveTab(i)}
            >
              <span className="rpt-modal-tab-num">{i + 1}</span>
              {t}
              {i === 0 && !tab1Valid && <span className="rpt-modal-tab-warn">●</span>}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="rpt-modal-body">

          {/* ── TAB 1: Job Information ── */}
          {activeTab === 0 && (
            <div className="rpt-modal-grid2">
              <Field label="Work Order / PM Ticket No." required>
                <Input value={job.workOrder} onChange={setJ('workOrder')} placeholder="e.g. WO-2026-0142" />
              </Field>
              <Field label="Site / Location" required>
                <Input value={job.site} onChange={setJ('site')} placeholder="e.g. Pump Station 3 — Zone A" />
              </Field>
              <Field label="Inspection Type">
                <Select value={job.inspType} onChange={setJ('inspType')}
                  options={['Routine', 'Predictive', 'Corrective', 'Emergency']} />
              </Field>
              <Field label="Shift">
                <Select value={job.shift} onChange={setJ('shift')}
                  options={['Day', 'Night', 'Other']} />
              </Field>
              <Field label="Shift Start Time">
                <Input value={job.shiftTime} onChange={setJ('shiftTime')} placeholder="e.g. 06:00" type="time" />
              </Field>
              <Field label="Date of Inspection">
                <Input value={job.date} onChange={setJ('date')} placeholder="DD/MM/YYYY" />
              </Field>
              <Field label="Inspector / Operator Name">
                <Input value={job.operatorName} onChange={setJ('operatorName')} placeholder="Full name" />
              </Field>
              <Field label="Contact Number">
                <Input value={job.contact} onChange={setJ('contact')} placeholder="Phone / extension" />
              </Field>
              <Field label="Department / Team">
                <Input value={job.department} onChange={setJ('department')} placeholder="e.g. Electrical Maintenance" />
              </Field>
            </div>
          )}

          {/* ── TAB 2: Equipment Nameplate ── */}
          {activeTab === 1 && (
            <div className="rpt-modal-two-cols">
              {/* Motor */}
              <div>
                <div className="rpt-modal-col-title">Motor (read from nameplate on site)</div>
                <div className="rpt-modal-grid1">
                  <Field label="Manufacturer"><Input value={motor.manufacturer} onChange={setM('manufacturer')} /></Field>
                  <Field label="Model / Type"><Input value={motor.model} onChange={setM('model')} /></Field>
                  <Field label="Serial No."><Input value={motor.serialNo} onChange={setM('serialNo')} /></Field>
                  <Field label="Frame Size (IEC)"><Input value={motor.frameSize} onChange={setM('frameSize')} placeholder="e.g. 160M" /></Field>
                  <Field label="Rated Power"><Input value={motor.ratedPower} onChange={setM('ratedPower')} /></Field>
                  <Field label="Voltage / Supply"><Input value={motor.voltage} onChange={setM('voltage')} /></Field>
                  <Field label="Rated Current (A)"><Input value={motor.ratedCurrent} onChange={setM('ratedCurrent')} /></Field>
                  <Field label="Rated Speed (RPM)"><Input value={motor.ratedSpeed} onChange={setM('ratedSpeed')} /></Field>
                  <Field label="Efficiency Class"><Select value={motor.effClass} onChange={setM('effClass')} options={['IE1', 'IE2', 'IE3', 'IE4', 'IE5', 'Other']} /></Field>
                  <Field label="Insulation Class"><Select value={motor.insulation} onChange={setM('insulation')} options={['Class A', 'Class B', 'Class F', 'Class H', 'Other']} /></Field>
                  <Field label="Duty Cycle"><Select value={motor.dutyCycle} onChange={setM('dutyCycle')} options={['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']} /></Field>
                  <Field label="Enclosure (IP)"><Input value={motor.enclosure} onChange={setM('enclosure')} placeholder="e.g. IP55 / TEFC" /></Field>
                  <Field label="Mounting"><Select value={motor.mounting} onChange={setM('mounting')} options={['B3 (Foot)', 'B5 (Flange)', 'B35 (Foot+Flange)', 'Other']} /></Field>
                  <Field label="Installation Date"><Input value={motor.installedDate} onChange={setM('installedDate')} placeholder="DD/MM/YYYY" /></Field>
                  <Field label="Total Operating Hours"><Input value={motor.operatingHours} onChange={setM('operatingHours')} placeholder="h" /></Field>
                  <Field label="Rewound?"><Select value={motor.rewound} onChange={setM('rewound')} options={['No', 'Yes']} /></Field>
                  {motor.rewound === 'Yes' && (
                    <Field label="Rewind Date"><Input value={motor.rewoundDate} onChange={setM('rewoundDate')} placeholder="DD/MM/YYYY" /></Field>
                  )}
                </div>
              </div>

              {/* Pump */}
              <div>
                <div className="rpt-modal-col-title">Pump</div>
                <div className="rpt-modal-grid1">
                  <Field label="Manufacturer"><Input value={pump.manufacturer} onChange={setP('manufacturer')} /></Field>
                  <Field label="Model / Type"><Input value={pump.model} onChange={setP('model')} /></Field>
                  <Field label="Serial No."><Input value={pump.serialNo} onChange={setP('serialNo')} /></Field>
                  <Field label="Flow Rate (m³/h)"><Input value={pump.flowRate} onChange={setP('flowRate')} /></Field>
                  <Field label="Total Head (m)"><Input value={pump.head} onChange={setP('head')} /></Field>
                  <Field label="Rated Speed (RPM)"><Input value={pump.ratedSpeed} onChange={setP('ratedSpeed')} /></Field>
                  <Field label="Impeller Dia. (mm)"><Input value={pump.impellerDia} onChange={setP('impellerDia')} /></Field>
                  <Field label="Seal Type"><Input value={pump.sealType} onChange={setP('sealType')} /></Field>
                  <Field label="Orientation"><Select value={pump.orientation} onChange={setP('orientation')} options={['Horizontal', 'Vertical']} /></Field>
                  <Field label="Installation Date"><Input value={pump.installedDate} onChange={setP('installedDate')} placeholder="DD/MM/YYYY" /></Field>
                </div>
              </div>
            </div>
          )}

          {/* ── TAB 3: Pre-Start Checklist ── */}
          {activeTab === 2 && (
            <div className="rpt-modal-grid2">
              <Field label="Supply Voltage L1–L2 (V)">
                <Input value={pre.vL1L2} onChange={setPK('vL1L2')} placeholder="e.g. 401" />
              </Field>
              <Field label="Supply Voltage L2–L3 (V)">
                <Input value={pre.vL2L3} onChange={setPK('vL2L3')} placeholder="e.g. 399" />
              </Field>
              <Field label="Supply Voltage L1–L3 (V)">
                <Input value={pre.vL1L3} onChange={setPK('vL1L3')} placeholder="e.g. 400" />
              </Field>
              <Field label="Supply Frequency (Hz)">
                <Input value={pre.freq} onChange={setPK('freq')} placeholder="e.g. 50.0" />
              </Field>
              <Field label="Insulation Resistance (MΩ) — 500V Megger">
                <Input value={pre.insulRes} onChange={setPK('insulRes')} placeholder="≥1 MΩ required" />
              </Field>
              <Field label="Earth Continuity (Ω)">
                <Input value={pre.earthCont} onChange={setPK('earthCont')} placeholder="<1 Ω required" />
              </Field>
              <Field label="Bearing Lubrication">
                <Select value={pre.lubrication} onChange={setPK('lubrication')} options={['OK', 'Not OK', 'N/A']} />
              </Field>
              <Field label="Cooling / Ventilation">
                <Select value={pre.cooling} onChange={setPK('cooling')} options={['OK', 'Not OK', 'N/A']} />
              </Field>
              <Field label="Guards & Safety Covers">
                <Select value={pre.guards} onChange={setPK('guards')} options={['OK', 'Not OK', 'N/A']} />
              </Field>
              <Field label="Coupling Alignment">
                <Select value={pre.coupling} onChange={setPK('coupling')} options={['OK', 'Not OK', 'N/A']} />
              </Field>
              <Field label="Motor Cleanliness">
                <Select value={pre.cleanliness} onChange={setPK('cleanliness')} options={['OK', 'Not OK', 'N/A']} />
              </Field>
              <Field label="Mounting Bolts Torqued">
                <Select value={pre.boltsTorque} onChange={setPK('boltsTorque')} options={['Yes', 'No', 'N/A']} />
              </Field>
            </div>
          )}
        </div>

        {/* Footer nav */}
        <div className="rpt-modal-footer">
          <div className="rpt-modal-nav-btns">
            {activeTab > 0 && (
              <button className="btn btn-ghost" onClick={() => setActiveTab((t) => t - 1)}>
                ← Previous
              </button>
            )}
            {activeTab < TABS.length - 1 && (
              <button className="btn btn-primary" onClick={() => setActiveTab((t) => t + 1)}>
                Next →
              </button>
            )}
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {!tab1Valid && (
              <span style={{ fontSize: 12, color: 'var(--warn)' }}>
                Work Order and Site are required (Tab 1)
              </span>
            )}
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={!allValid}
              style={{ opacity: allValid ? 1 : 0.45 }}
            >
              Generate Report ✓
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}
