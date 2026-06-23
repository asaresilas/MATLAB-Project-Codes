export function AlarmCenter({ alarms, onAcknowledge, onAcknowledgeAll, onClearResolved }) {
  return (
    <div className="alarm-center">
      <section className="panel">
        <div className="panel-header"><span>Active Alarms</span><span className="panel-subtle">{alarms.active.length} active</span></div>
        <div className="alarm-actions"><button type="button" className="secondary-button" onClick={onAcknowledgeAll}>Acknowledge warnings</button><button type="button" className="secondary-button" onClick={onClearResolved}>Clear resolved</button></div>
        <div className="alarm-list">
          {alarms.active.length === 0 ? <div className="empty-state">No active alarms</div> : alarms.active.map((alarm) => <div key={alarm.id} className={`alarm-item severity-${alarm.severity}`}><div className="alarm-main"><div className="alarm-code">{alarm.code}</div><div className="alarm-message">{alarm.message}</div></div><div className="alarm-meta"><span>{alarm.source}</span><span>{alarm.raisedAt}</span></div>{!alarm.acknowledged && <button type="button" className="ack-button" onClick={() => onAcknowledge(alarm.id)}>Acknowledge</button>}</div>)}
        </div>
      </section>
      <section className="panel"><div className="panel-header"><span>Event Log</span><span className="panel-subtle">{alarms.events.length} recent</span></div><div className="event-log">{alarms.events.map((event) => <div key={event.id} className="event-item"><div className="event-top"><span className="event-source">{event.source}</span><span className="event-time">{event.time}</span></div><div className="event-message">{event.message}</div></div>)}</div></section>
    </div>
  )
}
