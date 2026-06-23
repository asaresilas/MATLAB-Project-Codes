/**
 * MotorPumpSchematic
 * Displays the real motor-pump photograph with professional engineering
 * callout labels on left and right panels. Health state drives the
 * colour-coded status badge and border glow.
 */

const STATE = {
  NORMAL:   { colour: '#22c55e', glow: '0 0 20px rgba(34,197,94,0.30)',  border: '#22c55e' },
  WARNING:  { colour: '#fbbf24', glow: '0 0 20px rgba(251,191,36,0.30)', border: '#fbbf24' },
  CRITICAL: { colour: '#ef4444', glow: '0 0 28px rgba(239,68,68,0.45)',  border: '#ef4444' },
  UNKNOWN:  { colour: '#38bdf8', glow: 'none',                            border: '#38bdf8' },
}

const LEFT_LABELS = [
  { text: 'Terminal Box',        sub: '3-Phase Power Input' },
  { text: 'Cooling Fan Cover',   sub: 'NDE / Fan End' },
  { text: 'Motor Frame',         sub: 'TEFC · IP55 · IE3' },
  { text: 'Stator Windings',     sub: 'L1 · L2 · L3 (400 V)' },
]

const RIGHT_LABELS = [
  { text: 'Discharge Nozzle',    sub: 'Radial Outlet · PN16' },
  { text: 'Flexible Coupling',   sub: 'Shaft Transmission' },
  { text: 'Pump Volute Casing',  sub: 'Q = 45 m³/h · H = 32 m' },
  { text: 'Suction Inlet',       sub: 'Axial · End-Suction' },
]

export function MotorPumpSchematic({ healthState = 'unknown' }) {
  const key = (healthState || 'unknown').toUpperCase()
  const s   = STATE[key] ?? STATE.UNKNOWN

  const isFlashing = key === 'CRITICAL'

  return (
    <div
      className="motor-photo-wrap"
      style={{
        border:     `2px solid ${s.border}`,
        boxShadow:  s.glow,
        transition: 'box-shadow 0.5s ease, border-color 0.5s ease',
      }}
    >
      {/* ══════════════════════════════════════════════════════
          MAIN ANNOTATED IMAGE LAYOUT — three column grid
          Left labels | Centre image | Right labels
      ══════════════════════════════════════════════════════ */}
      <div className="mps-layout">

        {/* ── Left label column ── */}
        <div className="mps-labels mps-labels-left">
          {LEFT_LABELS.map(({ text, sub }, i) => (
            <div key={i} className="mps-callout mps-callout-left">
              <div className="mps-callout-text">
                <span className="mps-callout-main">{text}</span>
                <span className="mps-callout-sub">{sub}</span>
              </div>
              <div className="mps-callout-line">
                <span className="mps-callout-dot" style={{ background: s.colour }} />
              </div>
            </div>
          ))}
        </div>

        {/* ── Centre: photograph ── */}
        <div className="mps-image-col">
          {/* Health status badge */}
          <div
            className="mps-badge"
            style={{ borderColor: s.colour, color: s.colour }}
            role="status"
            aria-live="polite"
          >
            <span
              className="mps-badge-dot"
              style={{
                background: s.colour,
                animation: isFlashing
                  ? 'badgeFlash 0.8s infinite'
                  : key === 'NORMAL'
                    ? 'badgePulse 2.5s infinite'
                    : 'none',
              }}
            />
            {key === 'UNKNOWN' ? 'MONITORING…' : key}
          </div>

          {/* The real motor-pump photograph */}
          <img
            src="/motor-pump.png"
            alt="Squirrel-cage induction motor coupled to centrifugal pump on a common base frame — side elevation view"
            className="mps-photo"
            draggable={false}
          />

          {/* 3-phase colour indicator row */}
          <div className="mps-phase-row">
            <span className="mps-phase" style={{ color: '#ef4444' }}>⬤ L1</span>
            <span className="mps-phase" style={{ color: '#fbbf24' }}>⬤ L2</span>
            <span className="mps-phase" style={{ color: '#22c55e' }}>⬤ L3</span>
          </div>
        </div>

        {/* ── Right label column ── */}
        <div className="mps-labels mps-labels-right">
          {RIGHT_LABELS.map(({ text, sub }, i) => (
            <div key={i} className="mps-callout mps-callout-right">
              <div className="mps-callout-line">
                <span className="mps-callout-dot" style={{ background: s.colour }} />
              </div>
              <div className="mps-callout-text">
                <span className="mps-callout-main">{text}</span>
                <span className="mps-callout-sub">{sub}</span>
              </div>
            </div>
          ))}
        </div>

      </div>

      {/* ── Bottom spec legend ── */}
      <div className="mps-legend">
        <span className="mps-legend-item"><strong>Motor:</strong> 3-Phase SCIM · 400 V · 50 Hz · 1480 RPM · IE3 · IP55 / TEFC · S/N: SCIM-2024-001</span>
        <span className="mps-legend-sep" />
        <span className="mps-legend-item"><strong>Pump:</strong> End-Suction Centrifugal · Q = 45 m³/h · H = 32 m · PN16 · S/N: CP-2024-001</span>
        <span className="mps-legend-sep" />
        <span className="mps-legend-item"><strong>Base:</strong> Common Fabricated Steel Skid · Anchor-Bolted</span>
      </div>
    </div>
  )
}
