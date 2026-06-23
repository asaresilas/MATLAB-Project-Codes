/**
 * AlarmsPage
 * ISA-18.2 compliant alarm management panel.
 * Displays acknowledged vs unacknowledged alarm states with distinct
 * visual encoding, alarm rate KPI (alarms/h), and required operator
 * action for each alarm.
 */
import { useState, useMemo, useCallback } from 'react'

const SEVERITY_ORDER = { critical: 0, warning: 1, info: 2 }

/* ISA-18.2 §10 — required operator action per alarm code */
const OPERATOR_ACTIONS = {
  OVERHEAT:      'Reduce load or check cooling fan',
  VIBRATION:     'Inspect bearings and couplings',
  OVERCURRENT:   'Check load and motor windings',
  UNDERVOLT:     'Check supply transformer and cables',
  BEARING_FAULT: 'Schedule bearing replacement',
  STATOR_FAULT:  'Notify electrical engineer immediately',
  RUL_LOW:       'Plan maintenance within 48 h',
  DEFAULT:        'Investigate and report to engineer',
}

function getAction(alarm) {
  const code = (alarm.code || alarm.source || '').toUpperCase()
  for (const [key, action] of Object.entries(OPERATOR_ACTIONS)) {
    if (code.includes(key.replace('_', ''))) return action
  }
  /* Severity-based fallback */
  const sev = (alarm.severity || '').toLowerCase()
  if (sev === 'critical') return 'Notify engineer — escalate immediately'
  if (sev === 'warning')  return 'Monitor and acknowledge within 10 min'
  return OPERATOR_ACTIONS.DEFAULT
}

/* Count alarms raised in the last 60 minutes — ISA-18.2 §12 */
function calcAlarmRate(events) {
  if (!Array.isArray(events) || events.length === 0) return 0
  const cutoff = Date.now() - 60 * 60 * 1000
  return events.filter((e) => {
    const ts = new Date(e.raisedAt || e.timestamp || 0).getTime()
    return !isNaN(ts) && ts >= cutoff
  }).length
}

/* Alarm rate status per ISA-18.2 §12.3 (Manageable ≤6/h, High >6/h, Flood >12/h) */
function rateStatus(rate) {
  if (rate > 12) return { cls: 'err',  label: 'Flood'       }
  if (rate > 6)  return { cls: 'warn', label: 'High'        }
  return             { cls: 'ok',   label: 'Manageable'  }
}

function formatTime(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString([], {
      month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hour12: false,
    })
  } catch { return String(ts) }
}

/* ── SortTh must live outside the component so React doesn't remount the
   thead on every render (defining a component type inside another
   component creates a new type reference on each render cycle).         */
function SortTh({ col, sortCol, sortAsc, onSort, children }) {
  const isActive = sortCol === col
  return (
    <th
      onClick={() => onSort(col)}
      style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap' }}
      aria-sort={isActive ? (sortAsc ? 'ascending' : 'descending') : 'none'}
    >
      {children}
      {isActive && <span style={{ marginLeft: 4 }}>{sortAsc ? '↑' : '↓'}</span>}
    </th>
  )
}

export function AlarmsPage({ controller }) {
  const [filter,     setFilter]     = useState('all')
  const [sortCol,    setSortCol]    = useState('severity')
  const [sortAsc,    setSortAsc]    = useState(true)

  const { alarms, acknowledgeAlarm, acknowledgeAllWarnings, clearResolvedAlarms } = controller

  const active   = alarms?.active  ?? []
  const events   = alarms?.events  ?? []
  const resolved = events.filter((e) => e.cleared)

  const alarmRate  = useMemo(() => calcAlarmRate(events), [events])
  const { cls: rateCls, label: rateLabel } = rateStatus(alarmRate)

  const critCount       = active.filter((a) => a.severity?.toLowerCase() === 'critical').length
  const warnCount       = active.filter((a) => a.severity?.toLowerCase() === 'warning').length
  const unackedCount    = active.filter((a) => !a.acknowledged).length
  const unackedWarnings = active.filter((a) => !a.acknowledged && a.severity?.toLowerCase() === 'warning').length

  const all = useMemo(() => [
    ...active.map((a)   => ({ ...a, _state: a.acknowledged ? 'acked' : 'active' })),
    ...resolved.map((a) => ({ ...a, _state: 'resolved' })),
  ], [active, resolved])

  const filtered = useMemo(() => {
    const rows = filter === 'all'     ? all
      : filter === 'active'           ? all.filter((a) => a._state !== 'resolved')
      : filter === 'unacked'          ? all.filter((a) => a._state === 'active')
      : filter === 'resolved'         ? all.filter((a) => a._state === 'resolved')
      : all.filter((a) => a.severity?.toLowerCase() === filter)

    return [...rows].sort((a, b) => {
      let va, vb
      if (sortCol === 'severity') {
        va = SEVERITY_ORDER[a.severity?.toLowerCase()] ?? 9
        vb = SEVERITY_ORDER[b.severity?.toLowerCase()] ?? 9
      } else if (sortCol === 'time') {
        va = new Date(a.raisedAt || a.timestamp || 0).getTime()
        vb = new Date(b.raisedAt || b.timestamp || 0).getTime()
      } else {
        va = String(a[sortCol] || '')
        vb = String(b[sortCol] || '')
      }
      if (va < vb) return sortAsc ? -1 : 1
      if (va > vb) return sortAsc ?  1 : -1
      return 0
    })
  }, [all, filter, sortCol, sortAsc])

  const toggleSort = useCallback((col) => {
    if (sortCol === col) setSortAsc((v) => !v)
    else { setSortCol(col); setSortAsc(true) }
  }, [sortCol])

  return (
    <div className="alarms-page-shell">
      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <div className="page-title">Alarm Center</div>
          <div className="page-sub">
            {active.length === 0
              ? 'No active alarms — system normal'
              : [
                  critCount > 0 && `${critCount} critical`,
                  warnCount > 0 && `${warnCount} warning`,
                ].filter(Boolean).join(', ') + ' — requires attention'
            }
          </div>
        </div>

        {/* Alarm rate KPI — ISA-18.2 §12 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className={`alarm-rate-kpi alarm-rate-${rateCls}`} title="Alarm rate over last 60 minutes (ISA-18.2 §12.3)">
            <span className="alarm-rate-val">{alarmRate}</span>
            <span className="alarm-rate-unit">alm/h</span>
            <span className="alarm-rate-status">{rateLabel}</span>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            {unackedWarnings > 0 && (
              <button className="btn btn-ghost" onClick={acknowledgeAllWarnings} title="Acknowledge all unacknowledged warning-class alarms">
                Ack All Warnings ({unackedWarnings})
              </button>
            )}
            {resolved.length > 0 && (
              <button className="btn btn-ghost" onClick={clearResolvedAlarms}>
                Clear Resolved
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Filter buttons ── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        {[
          { id: 'all',      label: 'All' },
          { id: 'active',   label: `Active${active.length > 0 ? ` (${active.length})` : ''}` },
          { id: 'unacked',  label: `Unacknowledged${unackedCount > 0 ? ` (${unackedCount})` : ''}`, cls: unackedCount > 0 ? 'crit' : '' },
          { id: 'critical', label: 'Critical', cls: 'crit' },
          { id: 'warning',  label: 'Warning',  cls: 'warn' },
          { id: 'resolved', label: `Resolved${resolved.length > 0 ? ` (${resolved.length})` : ''}` },
        ].map(({ id, label, cls }) => (
          <button
            key={id}
            className={`filter-btn${filter === id ? ` active${cls ? ` ${cls}` : ''}` : ''}`}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}

        {/* ISA-18.2 legend */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, fontSize: 11, color: 'var(--txt-3)', alignItems: 'center' }}>
          <span><span className="alarm-state-dot active-dot" /> Unacked</span>
          <span><span className="alarm-state-dot acked-dot"  /> Acknowledged</span>
          <span><span className="alarm-state-dot resolved-dot" /> Resolved</span>
        </div>
      </div>

      {/* ── Alarm table ── */}
      {filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state" style={{ padding: '60px 20px' }}>
            <div className="empty-state-icon">✓</div>
            <div className="empty-state-text">No alarms in this view</div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ overflowX: 'auto' }}>
          <table className="alarm-table" aria-label="Alarm log">
            <thead>
              <tr>
                <SortTh col="severity" sortCol={sortCol} sortAsc={sortAsc} onSort={toggleSort}>Severity</SortTh>
                <SortTh col="message"  sortCol={sortCol} sortAsc={sortAsc} onSort={toggleSort}>Message</SortTh>
                <SortTh col="source"   sortCol={sortCol} sortAsc={sortAsc} onSort={toggleSort}>Source</SortTh>
                <th>Required Action</th>
                <SortTh col="time"     sortCol={sortCol} sortAsc={sortAsc} onSort={toggleSort}>Time</SortTh>
                <th>Status</th>
                <th aria-label="Acknowledge action"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((alarm, i) => {
                const sev    = alarm.severity?.toLowerCase() || 'info'
                const ts     = alarm.raisedAt || alarm.timestamp
                const isAcked    = alarm._state === 'acked'
                const isResolved = alarm._state === 'resolved'
                const rowCls = isResolved ? 'alarm-row-resolved'
                             : isAcked    ? 'alarm-row-acked'
                             :              'alarm-row-active'

                return (
                  <tr
                    key={alarm.id ?? alarm.code ?? i}
                    className={rowCls}
                    role="row"
                    aria-label={`${alarm.severity || 'Info'} alarm: ${alarm.message || ''}`}
                  >
                    {/* Severity */}
                    <td>
                      <span className={`alarm-severity ${sev}`}>{alarm.severity || 'Info'}</span>
                    </td>

                    {/* Message — with unacked left-border accent */}
                    <td style={{ maxWidth: 280 }}>
                      <span className={`alarm-message${!isAcked && !isResolved ? ' alarm-message-unacked' : ''}`}>
                        {alarm.message || '—'}
                      </span>
                    </td>

                    {/* Source / code */}
                    <td>
                      <span className="alarm-source">
                        {alarm.source || alarm.code || '—'}
                      </span>
                    </td>

                    {/* Required operator action — ISA-18.2 §10 */}
                    <td style={{ maxWidth: 240 }}>
                      <span className="alarm-action">
                        {getAction(alarm)}
                      </span>
                    </td>

                    {/* Time raised */}
                    <td>
                      <span className="alarm-time">{formatTime(ts)}</span>
                    </td>

                    {/* State badge */}
                    <td>
                      <span className={`alarm-state-badge alarm-state-${alarm._state}`}>
                        {isAcked ? '✓ ACK' : isResolved ? '◉ CLR' : '● ACTIVE'}
                      </span>
                    </td>

                    {/* Acknowledge button — only for unacked active alarms */}
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {alarm._state === 'active' && acknowledgeAlarm && (
                        <button
                          className="btn btn-ghost alarm-ack-btn"
                          onClick={() => acknowledgeAlarm(alarm.id ?? alarm.code)}
                          title="Acknowledge this alarm"
                          aria-label={`Acknowledge alarm: ${alarm.message}`}
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── ISA-18.2 §12 footnote ── */}
      <div style={{ marginTop: 12, fontSize: 10, color: 'var(--txt-3)', display: 'flex', gap: 16 }}>
        <span>Alarm rate ≤6/h = Manageable · 6–12/h = High · &gt;12/h = Flood (ISA-18.2 §12.3)</span>
        <span>All times in local timezone · Unacknowledged alarms require operator response</span>
      </div>
    </div>
  )
}
