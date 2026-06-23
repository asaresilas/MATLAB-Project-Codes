export function DigitalTwinPanel({ machine, application, operatingPoint }) {
  return (
    <section className="panel twin-panel">
      <div className="panel-header"><span>Digital Twin Asset State</span><span className="panel-subtle">{application.mode}</span></div>
      <div className="twin-layout">
        <div className="asset-diagram">
          <div className={`asset-shell health-${machine.healthState.toLowerCase()}`}>
            <div className="asset-rotor">Rotor</div>
            <div className="asset-stator">Stator</div>
            <div className="asset-bearing bearing-left">Bearing A</div>
            <div className="asset-bearing bearing-right">Bearing B</div>
          </div>
        </div>
        <div className="operating-grid">
          <div className="metric-card"><span className="field-label">RPM</span><strong>{operatingPoint.rpm}</strong></div>
          <div className="metric-card"><span className="field-label">Torque</span><strong>{operatingPoint.torque} Nm</strong></div>
          <div className="metric-card"><span className="field-label">Ambient</span><strong>{operatingPoint.ambient} C</strong></div>
          <div className="metric-card"><span className="field-label">Load</span><strong>{operatingPoint.load}</strong></div>
        </div>
      </div>
    </section>
  )
}
