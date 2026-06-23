import { GaugeRing } from './GaugeRing.jsx'

export function OperatingPointCard({ operatingPoint, machine }) {
  const rpm     = operatingPoint?.rpm
  const torque  = operatingPoint?.torque
  const ambient = operatingPoint?.ambient
  const load    = operatingPoint?.load

  const rpmNum    = parseFloat(rpm)
  const torqueNum = parseFloat(torque)

  const rpmValid    = !isNaN(rpmNum)
  const torqueValid = !isNaN(torqueNum)

  // ISO 10816-3 / rated specs: overspeed warn >1550 RPM, crit >1600 RPM; underspeed crit <1350 RPM
  const rpmStatus    = !rpmValid ? 'ok'
    : rpmNum > 1600 ? 'crit'
    : rpmNum > 1550 ? 'warn'
    : rpmNum < 1350 ? 'crit'
    : rpmNum < 1400 ? 'warn'
    : 'ok'
  // Rated torque 97.3 N·m (15 kW @ 1480 RPM); warn >110 N·m (113%), crit >130 N·m (134%)
  const torqueStatus = !torqueValid ? 'ok' : torqueNum > 130 ? 'crit' : torqueNum > 110 ? 'warn' : 'ok'

  const rows = [
    { label: 'Rated Speed',     value: '1480',   unit: 'RPM', note: 'Nameplate' },
    { label: 'Actual Speed',    value: rpmValid ? rpmNum.toFixed(0) : '--', unit: 'RPM', status: rpmStatus },
    { label: 'Rated Torque',    value: '97.3',   unit: 'N·m', note: 'Nameplate' },
    { label: 'Actual Torque',   value: torqueValid ? torqueNum.toFixed(1) : '--', unit: 'N·m', status: torqueStatus },
    { label: 'Supply Frequency',value: '50',     unit: 'Hz',  note: 'Nominal' },
    { label: 'Supply Voltage',  value: '400',    unit: 'V',   note: '3Ø L-L' },
    { label: 'Ambient Temp',    value: ambient != null && !isNaN(parseFloat(ambient)) ? parseFloat(ambient).toFixed(1) : '--', unit: '°C' },
    { label: 'Load Factor',     value: typeof load === 'number' ? `${(load * 100).toFixed(1)}` : (load ?? '--'), unit: typeof load === 'number' ? '%' : '' },
  ]

  const statusColor = (s) => s === 'crit' ? 'var(--crit)' : s === 'warn' ? 'var(--warn)' : 'var(--txt)'

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Operating Point</span>
        <span style={{ fontSize: 10, color: 'var(--txt-3)', fontFamily: 'var(--mono)' }}>
          IE3 / IP55 / TEFC
        </span>
      </div>

      {/* Speed + Torque gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 8px', borderRight: '1px solid var(--border)' }}>
          <GaugeRing
            value={rpmValid ? rpmNum : 0}
            max={1800}
            unit="RPM"
            label="Rotor Speed"
            status={rpmStatus}
            size={100}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 8px' }}>
          <GaugeRing
            value={torqueValid ? torqueNum : 0}
            max={160}
            unit="N·m"
            label="Shaft Torque"
            status={torqueStatus}
            size={100}
          />
        </div>
      </div>

      {/* Frequency + Voltage highlight */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--border)' }}>
        {[
          { label: 'Frequency', value: '50', unit: 'Hz', color: '#a78bfa' },
          { label: 'Supply Voltage', value: '400', unit: 'V', color: '#0ea5e9' },
        ].map(({ label, value, unit, color }) => (
          <div key={label} style={{
            padding: '12px 14px',
            borderRight: label === 'Frequency' ? '1px solid var(--border)' : 'none',
          }}>
            <div style={{ fontSize: 10, color: 'var(--txt-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>{label}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 3 }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 24, fontWeight: 700, color }}>{value}</span>
              <span style={{ fontSize: 12, color: 'var(--txt-3)' }}>{unit}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Remaining rows */}
      <div style={{ padding: '4px 14px 10px' }}>
        {rows.slice(4).map(({ label, value, unit, status, note }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontSize: 12, color: 'var(--txt-3)' }}>{label}</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              {note && <span style={{ fontSize: 9.5, color: 'var(--txt-3)', fontStyle: 'italic' }}>{note}</span>}
              <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: status ? statusColor(status) : 'var(--txt)' }}>{value}</span>
              <span style={{ fontSize: 11, color: 'var(--txt-3)' }}>{unit}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
