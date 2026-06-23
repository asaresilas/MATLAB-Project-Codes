function SensorCard({ title, value, unit, detail, freshness, tone }) {
  return <div className={`sensor-card tone-${tone}`}><div className="sensor-title">{title}</div><div className="sensor-value">{value} <span>{unit}</span></div><div className="sensor-detail">{detail}</div><div className="sensor-freshness">{freshness}</div></div>
}

export function SensorGrid({ sensors, signalQuality }) {
  return (
    <section className="panel">
      <div className="panel-header"><span>Sensor State Grid</span><span className="panel-subtle">{signalQuality.summary}</span></div>
      <div className="sensor-grid">
        <SensorCard title="Phase U Current" value={sensors.phaseCurrent.u.toFixed(2)} unit="A" detail={`Imbalance ${sensors.phaseCurrent.imbalance.toFixed(1)}%`} freshness={sensors.freshness} tone={sensors.phaseCurrent.imbalance > 10 ? 'danger' : sensors.phaseCurrent.imbalance > 4 ? 'warning' : 'success'} />
        <SensorCard title="Phase V Current" value={sensors.phaseCurrent.v.toFixed(2)} unit="A" detail={`Signal quality ${signalQuality.signalQuality}`} freshness={sensors.freshness} tone="info" />
        <SensorCard title="Phase W Current" value={sensors.phaseCurrent.w.toFixed(2)} unit="A" detail={`Packet status ${signalQuality.packetState}`} freshness={sensors.freshness} tone="info" />
        <SensorCard title="Vibration RMS" value={sensors.vibration.rms.toFixed(2)} unit="g" detail={`Crest ${sensors.vibration.crestFactor.toFixed(2)} | Kurtosis ${sensors.vibration.kurtosis.toFixed(2)}`} freshness={sensors.freshness} tone={sensors.vibration.rms > 0.8 ? 'danger' : sensors.vibration.rms > 0.4 ? 'warning' : 'success'} />
        <SensorCard title="Stator Temperature" value={sensors.temperature.stator.toFixed(1)} unit="C" detail={`Delta ${sensors.temperature.delta.toFixed(1)} C`} freshness={sensors.freshness} tone={sensors.temperature.stator > 85 ? 'danger' : sensors.temperature.stator > 65 ? 'warning' : 'success'} />
        <SensorCard title="Bearing Temperature" value={sensors.temperature.bearing.toFixed(1)} unit="C" detail={`Thermal state ${sensors.thermal.state}`} freshness={sensors.freshness} tone={sensors.temperature.bearing > 80 ? 'danger' : sensors.temperature.bearing > 60 ? 'warning' : 'success'} />
      </div>
    </section>
  )
}
