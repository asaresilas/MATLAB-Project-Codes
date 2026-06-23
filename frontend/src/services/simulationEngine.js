const scenarioLibrary = {
  healthy: { name: 'Healthy steady state', healthState: 'NORMAL', confidence: 96, uncertainty: 6, operatingPoint: { rpm: 1775, torque: 11.4, ambient: 27.2, load: 'Nominal' }, sensors: { phaseCurrent: { u: 14.1, v: 13.9, w: 14.0, imbalance: 1.4 }, vibration: { rms: 0.21, crestFactor: 2.1, kurtosis: 2.9, severity: 'Normal' }, temperature: { stator: 48.3, bearing: 42.6, delta: 5.7 }, thermal: { state: 'Nominal', hotSpot: 43.1 } }, fusionModel: 'Meta Fusion', rulHours: 18450 },
  drift: { name: 'Warning drift', healthState: 'WARNING', confidence: 81, uncertainty: 18, operatingPoint: { rpm: 1752, torque: 13.8, ambient: 29.4, load: 'High' }, sensors: { phaseCurrent: { u: 15.6, v: 14.7, w: 14.2, imbalance: 5.8 }, vibration: { rms: 0.54, crestFactor: 3.4, kurtosis: 4.7, severity: 'Warning' }, temperature: { stator: 71.2, bearing: 63.9, delta: 7.3 }, thermal: { state: 'Elevated', hotSpot: 70.5 } }, fusionModel: 'Meta Fusion', rulHours: 8600 },
  critical: { name: 'Critical onset', healthState: 'CRITICAL', confidence: 93, uncertainty: 11, operatingPoint: { rpm: 1690, torque: 16.5, ambient: 30.1, load: 'Peak' }, sensors: { phaseCurrent: { u: 17.4, v: 14.8, w: 12.9, imbalance: 13.6 }, vibration: { rms: 0.91, crestFactor: 4.9, kurtosis: 6.1, severity: 'Critical' }, temperature: { stator: 92.8, bearing: 88.4, delta: 4.4 }, thermal: { state: 'Hotspot', hotSpot: 96.3 } }, fusionModel: 'Meta Fusion', rulHours: 2100 },
}

export function createSimulationSample(scenarioKey, tick) {
  const scenario = scenarioLibrary[scenarioKey] || scenarioLibrary.healthy
  const oscillation = Math.sin(tick / 2.5) * 0.04
  return {
    sourceMode: 'SIMULATION',
    timestamp: new Date().toISOString(),
    alert_level: scenario.healthState,
    confidence: (scenario.confidence + oscillation) / 100,
    uncertainty: scenario.uncertainty / 100,
    model_used: `[${scenario.fusionModel}] ${scenario.name}`,
    inference_time_ms: 18 + Math.abs(Math.cos(tick)) * 4,
    machine: { machineId: 'SCIM-01', rulHours: Math.max(0, scenario.rulHours - tick * (scenario.healthState === 'CRITICAL' ? 18 : 4)) },
    sensors: {
      phaseCurrent: { u: scenario.sensors.phaseCurrent.u + oscillation, v: scenario.sensors.phaseCurrent.v + oscillation / 2, w: scenario.sensors.phaseCurrent.w - oscillation / 2, imbalance: scenario.sensors.phaseCurrent.imbalance + Math.abs(oscillation * 10) },
      vibration: { rms: scenario.sensors.vibration.rms + Math.abs(oscillation), crestFactor: scenario.sensors.vibration.crestFactor + Math.abs(oscillation * 6), kurtosis: scenario.sensors.vibration.kurtosis + Math.abs(oscillation * 8), severity: scenario.sensors.vibration.severity },
      temperature: { stator: scenario.sensors.temperature.stator + oscillation * 8, bearing: scenario.sensors.temperature.bearing + oscillation * 6, delta: scenario.sensors.temperature.delta + Math.abs(oscillation) },
      thermal: { state: scenario.sensors.thermal.state, hotSpot: scenario.sensors.thermal.hotSpot + oscillation * 7 },
    },
    operatingPoint: scenario.operatingPoint,
    models: {
      CWRU: { availability: 'available', predictedClass: scenario.healthState === 'NORMAL' ? 'Normal' : 'Bearing anomaly', confidence: scenario.confidence / 100, uncertainty: scenario.uncertainty / 100, latencyMs: 8 },
      Induction: { availability: 'available', predictedClass: scenario.healthState, confidence: (scenario.confidence - 3) / 100, uncertainty: (scenario.uncertainty + 2) / 100, latencyMs: 11 },
      NASA: { availability: 'available', predictedClass: `${scenario.rulHours}h`, confidence: 0.72, uncertainty: 0.18, latencyMs: 14 },
      Current: { availability: 'available', predictedClass: scenario.healthState === 'CRITICAL' ? 'Imbalance' : 'Stable', confidence: (scenario.confidence - 6) / 100, uncertainty: (scenario.uncertainty + 4) / 100, latencyMs: 7 },
      Thermal: { availability: 'available', predictedClass: scenario.sensors.thermal.state, confidence: (scenario.confidence - 4) / 100, uncertainty: (scenario.uncertainty + 1) / 100, latencyMs: 12 },
    },
  }
}
