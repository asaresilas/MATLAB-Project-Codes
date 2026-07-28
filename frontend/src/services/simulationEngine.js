const scenarioLibrary = {
  // 75 kW, 400 V, 50 Hz, 4-pole SCIM — motor_params_normal.m conditions
  healthy: { name: 'Healthy steady state', healthState: 'NORMAL', confidence: 96, uncertainty: 6, operatingPoint: { rpm: 1480, torque: 315.0, ambient: 40.0, load: 'Nominal (65%)' }, sensors: { phaseCurrent: { u: 85.0, v: 85.0, w: 85.0, imbalance: 1.4 }, vibration: { rms: 0.05, crestFactor: 2.1, kurtosis: 2.9, severity: 'Normal' }, temperature: { stator: 60.0, bearing: 50.0, delta: 20.0 }, thermal: { state: 'Nominal', hotSpot: 55.0 } }, fusionModel: 'Meta Fusion', rulHours: 18450 },
  // motor_params_fault.m conditions: early bearing defect + shaft misalignment
  drift: { name: 'Warning drift', healthState: 'WARNING', confidence: 81, uncertainty: 18, operatingPoint: { rpm: 1465, torque: 406.0, ambient: 40.0, load: 'High (83%)' }, sensors: { phaseCurrent: { u: 110.0, v: 108.0, w: 109.0, imbalance: 5.8 }, vibration: { rms: 1.2, crestFactor: 4.1, kurtosis: 6.8, severity: 'Warning' }, temperature: { stator: 95.0, bearing: 75.0, delta: 55.0 }, thermal: { state: 'Elevated', hotSpot: 90.0 } }, fusionModel: 'Meta Fusion', rulHours: 8600 },
  // motor_params_critical.m conditions: severe bearing + overtemperature + overload
  critical: { name: 'Critical onset', healthState: 'CRITICAL', confidence: 93, uncertainty: 11, operatingPoint: { rpm: 1440, torque: 522.0, ambient: 40.0, load: 'Peak (108%)' }, sensors: { phaseCurrent: { u: 138.0, v: 134.0, w: 130.0, imbalance: 13.6 }, vibration: { rms: 4.0, crestFactor: 6.2, kurtosis: 9.8, severity: 'Critical' }, temperature: { stator: 130.0, bearing: 100.0, delta: 90.0 }, thermal: { state: 'Hotspot', hotSpot: 125.0 } }, fusionModel: 'Meta Fusion', rulHours: 2100 },
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
