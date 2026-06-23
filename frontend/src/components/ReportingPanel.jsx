export function ReportingPanel({ machine, alarms, diagnostics, defaultFormat, onExport }) {
  return (
    <section className="panel reporting-panel">
      <div className="panel-header"><span>Reporting</span><span className="panel-subtle">Auditable session export</span></div>
      <div className="reporting-body">
        <div className="report-stat-grid">
          <div className="metric-card"><span className="field-label">Health state</span><strong>{machine.healthState}</strong></div>
          <div className="metric-card"><span className="field-label">Active alarms</span><strong>{alarms.active.length}</strong></div>
          <div className="metric-card"><span className="field-label">Event records</span><strong>{alarms.events.length}</strong></div>
          <div className="metric-card"><span className="field-label">Avg latency</span><strong>{diagnostics.avgLatencyMs} ms</strong></div>
        </div>
        <div className="report-actions">
          <button type="button" className="primary-button" onClick={() => onExport(defaultFormat)}>Export {defaultFormat.toUpperCase()}</button>
          <button type="button" className="secondary-button" onClick={() => onExport(defaultFormat === 'json' ? 'csv' : 'json')}>Export {defaultFormat === 'json' ? 'CSV' : 'JSON'}</button>
        </div>
      </div>
    </section>
  )
}
