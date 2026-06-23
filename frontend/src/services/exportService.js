const triggerDownload = (filename, contents, type) => {
  const blob = new Blob([contents], { type })
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.URL.revokeObjectURL(url)
}

export function exportSessionAsJson(snapshot) {
  const filename = `dt-session-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
  triggerDownload(filename, JSON.stringify(snapshot, null, 2), 'application/json')
}

export function exportSessionAsCsv(snapshot) {
  const rows = [
    ['timestamp', 'machineId', 'healthState', 'predictionCertainty', 'uncertainty', 'rulHours', 'connectionState', 'backendState', 'avgLatencyMs'],
    [
      snapshot.exportedAt,
      snapshot.machine.machineId,
      snapshot.machine.healthState,
      snapshot.machine.predictionCertainty,
      snapshot.machine.uncertainty,
      snapshot.machine.rulHours,
      snapshot.application.connectionState,
      snapshot.diagnostics.backendState,
      snapshot.diagnostics.avgLatencyMs,
    ],
    [],
    ['activeAlarms'],
    ['code', 'severity', 'source', 'message', 'raisedAt', 'acknowledged'],
    ...snapshot.alarms.active.map((alarm) => [alarm.code, alarm.severity, alarm.source, alarm.message, alarm.raisedAt, alarm.acknowledged]),
    [],
    ['recentEvents'],
    ['time', 'source', 'message'],
    ...snapshot.alarms.events.map((event) => [event.time, event.source, event.message]),
  ]
  const csv = rows.map((row) => row.map((cell) => `"${String(cell ?? '').replaceAll('"', '""')}"`).join(',')).join('\n')
  const filename = `dt-session-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`
  triggerDownload(filename, csv, 'text/csv;charset=utf-8')
}
