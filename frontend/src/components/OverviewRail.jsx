import { StatusBadge } from './StatusBadge.jsx'

export function OverviewRail({ machine, application, recommendation }) {
  return (
    <div className="overview-rail">
      <section className="panel health-panel">
        <div className="panel-header">
          <span>Health Overview</span>
          <StatusBadge label={machine.healthState} tone={machine.healthState === 'NORMAL' ? 'success' : machine.healthState === 'WARNING' ? 'warning' : machine.healthState === 'CRITICAL' ? 'danger' : 'neutral'} />
        </div>
        <div className="health-score">{machine.predictionCertainty != null ? `${machine.predictionCertainty.toFixed(0)}` : '—'}%</div>
        <div className="health-label">Prediction certainty (per inference)</div>
        <div className="overview-metrics">
          <div className="metric-card"><span className="field-label">Uncertainty</span><strong>{machine.uncertainty}%</strong></div>
          <div className="metric-card"><span className="field-label">RUL</span><strong>{machine.rulHours} h</strong></div>
          <div className="metric-card"><span className="field-label">Recommended action</span><strong>{recommendation}</strong></div>
        </div>
      </section>
      <section className="panel"><div className="panel-header"><span>Machine State</span></div><dl className="definition-list"><div><dt>Machine state</dt><dd>{machine.healthState}</dd></div><div><dt>Decision engine</dt><dd>{machine.modelUsed}</dd></div><div><dt>Last inference</dt><dd>{machine.lastInferenceText}</dd></div><div><dt>Last data packet</dt><dd>{machine.lastPacketText}</dd></div></dl></section>
      <section className="panel"><div className="panel-header"><span>Application State</span></div><dl className="definition-list"><div><dt>Mode</dt><dd>{application.mode}</dd></div><div><dt>Connection</dt><dd>{application.connectionState}</dd></div><div><dt>Data stream</dt><dd>{application.dataState}</dd></div><div><dt>Backend</dt><dd>{application.backendState}</dd></div></dl></section>
    </div>
  )
}
