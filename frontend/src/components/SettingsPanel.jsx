export function SettingsPanel({ settings, onUpdate, role }) {
  const isEditable = role === 'admin' || role === 'engineer'

  return (
    <section className="panel settings-panel">
      <div className="panel-header"><span>Settings</span><span className="panel-subtle">Thresholds and export defaults</span></div>
      <div className="settings-grid">
        <label>
          <span className="field-label">Machine label</span>
          <input value={settings.machineLabel} onChange={(event) => onUpdate({ machineLabel: event.target.value })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Stale data timeout (ms)</span>
          <input type="number" value={settings.staleDataMs} onChange={(event) => onUpdate({ staleDataMs: Number(event.target.value) || 0 })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Imbalance warning (%)</span>
          <input type="number" value={settings.currentImbalanceWarning} onChange={(event) => onUpdate({ currentImbalanceWarning: Number(event.target.value) || 0 })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Imbalance critical (%)</span>
          <input type="number" value={settings.currentImbalanceCritical} onChange={(event) => onUpdate({ currentImbalanceCritical: Number(event.target.value) || 0 })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Temperature warning (C)</span>
          <input type="number" value={settings.temperatureWarning} onChange={(event) => onUpdate({ temperatureWarning: Number(event.target.value) || 0 })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Temperature critical (C)</span>
          <input type="number" value={settings.temperatureCritical} onChange={(event) => onUpdate({ temperatureCritical: Number(event.target.value) || 0 })} disabled={!isEditable} />
        </label>
        <label>
          <span className="field-label">Default export</span>
          <select value={settings.exportFormat} onChange={(event) => onUpdate({ exportFormat: event.target.value })}>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </label>
        <div className="settings-note">
          {isEditable ? 'Changes save locally and affect alarm interpretation immediately.' : 'Operator role can view settings but cannot edit thresholds.'}
        </div>
      </div>
    </section>
  )
}
