import { useState } from 'react'

const SECTIONS = [
  {
    id: 'overview',
    icon: '⚙',
    title: 'System Overview',
    color: '#0ea5e9',
    content: [
      {
        heading: 'What is MotorGuard Digital Twin?',
        text: `MotorGuard is a real-time predictive maintenance console for a squirrel-cage induction motor coupled to a centrifugal pump. It continuously monitors the motor-pump assembly, analyses sensor data using AI-based health models, and alerts operators to potential faults before they cause unplanned downtime.

The system combines five specialised signal-processing models — covering vibration, stator current, temperature imaging, bearing wear, and motor inductance — into a single fused health assessment. This multi-model approach gives higher accuracy than any single sensor alone.`,
      },
      {
        heading: 'How data flows',
        text: `1. The MATLAB/Simulink digital twin collects sensor samples every second.
2. Samples are sent to the FastAPI backend over a WebSocket connection.
3. The backend runs all five expert models and a meta-fusion layer, then returns a health classification (NORMAL / WARNING / CRITICAL) and a Remaining Useful Life estimate.
4. This console receives the result and displays it in real time.
5. When the backend is unavailable, the console switches to Simulation Mode, replaying a representative motor scenario so operators can still practice using the interface.`,
      },
    ],
  },
  {
    id: 'dashboard',
    icon: '⬛',
    title: 'Dashboard Page',
    color: '#0ea5e9',
    content: [
      {
        heading: 'Motor Status & Health Badge',
        text: `The motor-pump schematic at the top left shows the physical assembly: the TEFC (Totally Enclosed Fan Cooled) induction motor on the left, the flexible coupling in the middle, and the centrifugal pump on the right.

The coloured ring and badge below the schematic indicate the current health state:
• GREEN — NORMAL: All parameters within acceptable limits. Continue normal operation.
• AMBER — WARNING: One or more parameters approaching a limit. Schedule inspection soon.
• RED — CRITICAL: A fault condition has been detected. Immediate attention required.

The Confidence percentage shows how certain the AI system is about its diagnosis. Values above 85% are highly reliable. Lower values may occur during sensor degradation or unusual operating conditions.`,
      },
      {
        heading: 'Motor Parameters Panel',
        text: `This panel shows the key nameplate and live operating parameters of the motor-pump unit:
• Machine ID — the unique identifier of this asset in the maintenance system.
• Speed (RPM) — actual rotor speed as measured by the tachometer or estimated from current signatures. Rated speed is 1480 RPM for a 4-pole, 50 Hz motor.
• Stator Temperature — temperature inside the motor windings. Sustained temperatures above 75 °C accelerate insulation ageing; above 90 °C risks permanent damage.
• Bearing Temperature — temperature at the drive-end and non-drive-end bearings. Rising bearing temperature is one of the earliest indicators of bearing wear or lubrication failure.
• Vibration RMS — root-mean-square of the vibration acceleration signal. Increasing RMS is a classic indicator of imbalance, misalignment, or bearing defects.
• Phase Current — RMS current in one phase (Phase U). Abnormal current waveforms indicate stator or rotor faults.`,
      },
      {
        heading: 'KPI Metric Cards',
        text: `The four metric cards below the schematic give instant at-a-glance readings of the most critical health indicators. Each card has a coloured top bar following the ISA-101 standard:
• Blue — informational reading, no threshold concern.
• Green — within normal safe limits.
• Amber — approaching a warning threshold.
• Red — at or above a critical threshold.

Remaining Useful Life (RUL) is the estimated number of operating hours before the motor-pump will require maintenance or replacement of a component. It is derived from historical degradation data using a deep learning model trained on real bearing run-to-failure datasets.`,
      },
      {
        heading: 'Trend Sparklines',
        text: `The two mini-charts at the bottom of the dashboard show the last 30 readings of vibration RMS and stator temperature. Use these to spot trends quickly:
• A steadily rising vibration sparkline suggests progressive bearing wear.
• A temperature spike that recovers suggests a transient overload.
• Oscillating values that remain flat over time suggest steady-state normal operation.
For detailed trend analysis with axis labels and time windows, open the Trends page from the sidebar.`,
      },
    ],
  },
  {
    id: 'sensors',
    icon: '◉',
    title: 'Live Sensors Page',
    color: '#22c55e',
    content: [
      {
        heading: 'Key Indicator Gauges',
        text: `The four circular gauge rings at the top show the most critical real-time readings. Each gauge arc fills from left to right as the value increases toward its maximum. The arc colour changes automatically with the ISA-101 standard:
• Green arc — value is within the normal operating band.
• Amber arc — value has crossed the warning threshold.
• Red arc — value has crossed the critical threshold.

The numeric value and engineering unit are shown in the centre of each gauge ring.`,
      },
      {
        heading: 'All Channels Grid',
        text: `Below the gauges, every instrumented signal is shown as a sensor card. Each card displays:
• Signal name — the physical quantity being measured.
• Numeric value — the latest reading with two decimal places.
• Status dot — green/amber/red in the top-right corner matching ISA-101.
• Progress bar — shows where the current value sits between the sensor's minimum and maximum range. The colour of the bar follows the same threshold logic as the gauge.
• Range labels — minimum and maximum values of the expected operating range.`,
      },
      {
        heading: 'Signal Quality Indicator',
        text: `The Signal Quality label in the top-right of the page header tells you the reliability of the incoming data:
• Nominal — live data is being received and validated correctly from the motor.
• Degraded — the data stream is present but packets are arriving late, dropping samples, or showing sensor read errors.
• Unknown — the system is in simulation mode or no valid data has been received yet.

If Signal Quality drops to Degraded during live operation, check the sensor wiring, the MATLAB/Simulink model, and the network connection between the controller and this console.`,
      },
      {
        heading: 'Sensor channel definitions',
        text: `Vibration RMS (g): Root-mean-square acceleration from an accelerometer mounted on the bearing housing. ISO 10816 specifies alarm levels based on machine class.

Crest Factor: Ratio of peak vibration to RMS. A high crest factor (>6) indicates impulsive events such as bearing spalling or gear tooth damage, even when RMS is still moderate.

Kurtosis: Statistical measure of the "peakiness" of the vibration signal. Healthy bearings have kurtosis ≈ 3. Values above 10 indicate developing defects.

Stator Temperature (°C): Thermocouple embedded in or near the stator windings. Motor insulation class defines the maximum allowable temperature (Class F = 155 °C, Class H = 180 °C, but operating well below these maximums extends life).

Phase Current (A): RMS current drawn by each phase. An imbalance between phases of more than 5% indicates a possible stator inter-turn short, broken rotor bar, or supply voltage imbalance.

Current Imbalance (%): Percentage difference between the highest and lowest phase currents relative to the average. A value above 8% is a warning; above 12% is critical (per IEC 60034-26 derating guidance).`,
      },
    ],
  },
  {
    id: 'trends',
    icon: '↗',
    title: 'Trend Analysis Page',
    color: '#a78bfa',
    content: [
      {
        heading: 'Reading the trend charts',
        text: `Each trend chart plots a sensor parameter over the last N samples. The horizontal axis represents time (older data on the left, newest on the right). The vertical axis shows the engineering value with labelled tick marks.

Key annotations on each chart:
• Maximum value label — shown in the chart colour at the highest point of the line.
• Minimum value label — shown in grey at the lowest point of the line.
• Latest value — shown as a filled circle at the rightmost point, and as a number in the card header.
• Delta indicator — in the header, the change from the first to the last reading in the current window is shown in green (falling) or amber (rising). A rising trend in vibration or temperature is always significant.`,
      },
      {
        heading: 'Time window selector',
        text: `Use the filter buttons at the top right to change the time window:
• 5 min — shows the last 5 minutes of data; useful for examining a sudden event in detail.
• 15 min — the default view; good for monitoring short-term drift.
• 1 hr — useful for shift handover and spotting gradual degradation.
• 6 hr — shows medium-term trends; helps confirm whether a warning is persistent or transient.

The window selector applies to all trend charts simultaneously.`,
      },
      {
        heading: 'What to look for in trends',
        text: `Normal behaviour: All channels show relatively flat lines with small random variation around a stable mean. Temperature may show a gentle rise during the first 20–30 minutes of operation (warm-up period) and then stabilise.

Early warning patterns:
• Gradual upward trend in Vibration RMS — suggests progressive bearing wear or developing imbalance.
• Gradual upward trend in Temperature that does not stabilise — suggests blocked ventilation, lubrication failure, or overloading.
• Current RMS increasing at constant load — can indicate rotor bar damage or winding degradation.
• Confidence (%) decreasing — the AI model is becoming uncertain; multiple sensor readings may be contradicting each other.

Acute fault patterns:
• Sudden step change in Vibration RMS — suggests a component fracture or severe imbalance event.
• Sudden spike in Temperature — suggests a cooling system failure or locked rotor event.
• RUL dropping rapidly — the degradation model detects accelerated wear.`,
      },
    ],
  },
  {
    id: 'alarms',
    icon: '⚠',
    title: 'Alarm Center',
    color: '#ef4444',
    content: [
      {
        heading: 'Alarm severity levels',
        text: `Every alarm is classified by severity following the ISA-18.2 alarm management standard:

CRITICAL (Red): A condition that could cause immediate damage to equipment, loss of containment, or safety hazard. Requires immediate action by the operator. Do not ignore or delay.

WARNING (Amber): A condition that is approaching a limit or shows a developing trend that requires attention within a reasonable timeframe. Investigate and plan corrective action.

INFO (Blue): An informational event — for example, the system switching between Live and Simulation modes, or a sensor being reconnected after a communications dropout.`,
      },
      {
        heading: 'Active vs resolved alarms',
        text: `Active alarms are fault conditions that currently exist. The Acknowledge (Ack) button records that an operator has seen and noted the alarm — it does NOT clear it. The alarm remains active until the underlying fault condition is resolved.

Resolved alarms (shown in the Resolved filter) are events that were previously active but have since cleared — either because the parameter returned within limits or a sensor reconnected. Reviewing resolved alarms helps identify intermittent faults.

Use "Acknowledge Warnings" to batch-acknowledge all warning-level alarms at once. Use "Clear Resolved" to remove cleared alarms from the event log and keep the view uncluttered.`,
      },
      {
        heading: 'Responding to alarms',
        text: `CRITICAL alarms — take these steps:
1. Acknowledge the alarm to record your response time.
2. Assess the fault message and source to understand which component is affected.
3. If vibration or temperature: consider reducing load or shutting down the motor to prevent damage.
4. Inspect the indicated component (bearing, winding, coupling) at the next safe opportunity.
5. Do not restart the motor without identifying and correcting the root cause.

WARNING alarms — take these steps:
1. Acknowledge and record the alarm in your maintenance log.
2. Monitor the trend for the affected parameter over the next hour.
3. If the trend is worsening, escalate to a CRITICAL response.
4. Plan a scheduled inspection within the current maintenance cycle.

The alarm source column identifies which sensor or model generated the alarm (e.g. Thermal, Current Signature, NASA/RUL, Transport) so you can direct investigation to the correct part of the system.`,
      },
    ],
  },
  {
    id: 'settings',
    icon: '⚙',
    title: 'Settings Page',
    color: '#f59e0b',
    content: [
      {
        heading: 'Notification toggles',
        text: `Critical alarms: Always enabled by default and strongly recommended. Disabling this means the console will not generate an alarm entry when a CRITICAL condition is detected.

Warning alarms: Enabled by default. Can be disabled in situations where a specific warning is known to be a false positive pending sensor calibration.

Sound alerts: When enabled, a short audio tone plays on each new alarm. Requires the browser to allow audio autoplay for this page.`,
      },
      {
        heading: 'Display settings',
        text: `Trend window: Sets the default time window shown on the Trends page and the dashboard sparklines. Changing this here also updates the trend charts immediately.

Update rate: How frequently the UI refreshes the displayed values. 1 second is the recommended default. Faster rates (500 ms) increase CPU usage in the browser. Slower rates (5 s) reduce network load but make the display less responsive.

Export format: The format used when generating reports from the reporting function — PDF for human-readable reports, CSV for spreadsheet analysis, JSON for integration with other systems.`,
      },
      {
        heading: 'Alarm thresholds (Engineer role required)',
        text: `These settings are visible only to users with Engineer or Administrator roles and allow you to adjust the alarm trigger levels to match the specific motor-pump installation:

Vibration thresholds are in g (gravitational acceleration units). The defaults (Warning: 5 g, Critical: 8 g) are based on ISO 10816-3 severity zones for motors of this size class.

Temperature thresholds are in degrees Celsius. The defaults (Warning: 75 °C, Critical: 90 °C) are set conservatively below the Class F insulation limit of 155 °C to account for the motor operating continuously at full load.

RUL alert threshold: When the predicted Remaining Useful Life drops below this number of hours, a warning alarm is generated so maintenance can be planned in advance.

Important: Do not set thresholds above the motor manufacturer's specified limits. Always consult the motor datasheet and your maintenance engineer before changing these values.`,
      },
    ],
  },
  {
    id: 'colors',
    icon: '◆',
    title: 'ISA-101 Colour Standard',
    color: '#22c55e',
    content: [
      {
        heading: 'Why standardised colours matter',
        text: `This console follows the ISA-101 Human-Machine Interface (HMI) standard — the internationally recognised colour coding for industrial control systems. Standardised colours reduce operator error because the meaning of a colour is consistent across all equipment in a plant.

The ISA-101 philosophy is "less colour is more". Most of the interface is presented in neutral dark tones. Colour is used sparingly and only to communicate process status. This means that when a colour does appear, it immediately draws the eye without visual fatigue from overuse.`,
      },
      {
        heading: 'Colour meanings at a glance',
        text: `GREEN (#22c55e) — Normal / Safe
The parameter is within its normal operating range. No action required.

AMBER / YELLOW (#f59e0b) — Warning / Abnormal
The parameter is approaching a limit or has crossed a warning threshold. Attention and investigation are required. Do not ignore.

RED (#ef4444) — Critical / Emergency / Fault
A critical threshold has been crossed, or a fault condition exists. Immediate action is required. In ISA-101, red is never used for decorative purposes — it always means a real problem exists.

BLUE (#0ea5e9) — Informational / Neutral
Used for general interface elements, informational messages, and neutral system status. Does not imply a process condition.

GREY / DARK — Inactive / Unknown
Used when a sensor has no data, a system is offline, or a state is indeterminate.`,
      },
      {
        heading: 'Status indicators on this console',
        text: `Connection pill (top right): The coloured pill next to "Live" / "Reconnecting" / "Offline" shows the WebSocket connection to the backend:
• Green + pulsing dot = Live data streaming normally.
• Amber = Connection interrupted, attempting to reconnect.
• Red = Connection failed or backend unreachable.
• Grey = System starting up or no connection attempted yet.

Health badge (Dashboard): The large badge showing NORMAL / WARNING / CRITICAL uses the ISA-101 colours and pulses with an animated ring when in CRITICAL state to ensure it cannot be missed.

Metric card top bars: The 2-pixel colour stripe at the top of each KPI card summarises the status of that specific parameter at a glance without requiring the operator to read the number.

Sensor status dots: The small dot in the top-right corner of each sensor card provides instant ISA-101 colour coding for that channel.`,
      },
    ],
  },
  {
    id: 'rul',
    icon: '⏱',
    title: 'Remaining Useful Life (RUL)',
    color: '#a78bfa',
    content: [
      {
        heading: 'What RUL means',
        text: `Remaining Useful Life (RUL) is the estimated number of hours of continued safe operation before a motor component is predicted to reach end-of-life and will require maintenance or replacement. RUL is expressed in hours on this console.

A high RUL (e.g. 2000 h) means the motor is in good condition and unlikely to fail soon. A low RUL (e.g. 50 h) means maintenance should be planned urgently.

RUL is a prediction, not a certainty. The actual life remaining depends on operating conditions continuing to be similar to the training data. Changes in load, environment, or maintenance practices will affect the actual outcome.`,
      },
      {
        heading: 'How RUL is calculated',
        text: `The RUL model is a Bidirectional LSTM with Attention (Bi-LSTM-Attn) neural network trained on the NASA PRONOSTIA bearing run-to-failure dataset. This dataset contains accelerometer data from bearings operated to failure under controlled conditions.

The model processes a sequence of 30 consecutive time windows, each described by 9 statistical features of the vibration signal (RMS, Kurtosis, Crest Factor, etc.). It predicts the number of remaining operating hours before bearing failure would be expected.

Key performance figures: Mean Absolute Error = 23.0 hours, Root Mean Squared Error = 26.8 hours, on a held-out test set of 300 samples. The model achieves R² = 0.9964 on the per-bearing NASA test set.

Important: The RUL estimate applies primarily to the motor bearings (the component with the most degradation data). Electrical insulation degradation or seal wear may not be fully reflected in the vibration-based RUL.`,
      },
      {
        heading: 'RUL thresholds and maintenance planning',
        text: `As a guide for maintenance planning:
• RUL > 500 h: No immediate action. Continue normal monitoring.
• RUL 150–500 h: Plan a scheduled inspection at the next maintenance window. Order any commonly replaced parts (bearings, mechanical seal kit) to have them available.
• RUL 50–150 h: A warning alarm is generated. Inspect the motor-pump unit within the current maintenance cycle. Prepare for bearing replacement.
• RUL < 50 h: A critical alarm is generated. Imminent failure risk. Plan for immediate shutdown and maintenance at the next available opportunity. Consider keeping a spare unit ready.

The RUL alert threshold can be adjusted on the Settings page by an Engineer to match your plant's maintenance intervals.`,
      },
    ],
  },
  {
    id: 'faq',
    icon: '?',
    title: 'Frequently Asked Questions',
    color: '#0ea5e9',
    content: [
      {
        heading: 'The console shows "Simulation" — is this normal?',
        text: `Yes. When the backend server (FastAPI) is not reachable — for example, when the MATLAB model is not running — the console automatically switches to Simulation Mode. In Simulation Mode, it replays a representative motor operating scenario so you can continue to explore and practice using the interface. All sensor values, alarms, and trends in Simulation Mode are synthetic and do not represent the actual motor state.

When the backend becomes available again, the console will automatically reconnect and switch back to Live Mode. You can also manually switch modes using the mode selector if visible in your installation.`,
      },
      {
        heading: 'What does "Confidence" mean and when should I be concerned?',
        text: `The Confidence value (0–100%) shows how certain the AI health assessment system is about its current diagnosis. It is derived from the probability distribution output of the meta-fusion model across the three health states.

High confidence (>85%) means the model's evidence from all sensor channels is consistent and pointing strongly to one health state.

Low confidence (<60%) means the sensor channels are giving conflicting evidence — for example, vibration looks normal but temperature is elevated, or the signal quality is degraded. In this case, treat the health classification with caution and rely on individual sensor readings on the Sensors page.

Very low confidence is itself a reason to investigate: it often indicates a sensor fault, communications problem, or an unusual operating condition not well represented in the training data.`,
      },
      {
        heading: 'An alarm appeared but the motor seems fine — what should I do?',
        text: `False positives can occur, particularly in Warning-level alarms, for several reasons:
• Transient events: A momentary load spike or a brief supply voltage fluctuation can trigger a warning that clears by itself. Check the Trends page to see if the parameter returned to normal.
• Sensor calibration drift: If a sensor is giving slightly higher readings than the actual value, it may trigger thresholds early. Compare readings with any portable instruments available.
• Unusual but benign operating conditions: Starting under heavy load, operating in extreme ambient temperatures, or running at unusual speeds can cause parameters to approach thresholds temporarily.

Acknowledge the alarm, note the time, and monitor the Trends page for the next 15–30 minutes. If the parameter stabilises and returns to normal, the alarm was likely a transient event. If it persists or worsens, investigate further.`,
      },
      {
        heading: 'What is the difference between Live and Simulation mode?',
        text: `Live Mode: The console receives real sensor data from the motor-pump assembly via the MATLAB/Simulink digital twin and the FastAPI backend. All displayed values, alarms, and RUL estimates reflect the actual condition of the physical motor.

Simulation Mode: The console plays back a scripted scenario (healthy, drifting, or critical) using synthetic data generated by the digital twin model. Useful for training operators, demonstrating the system, or testing the console when the physical motor is not running.

The connection status pill in the top-right corner of the topbar always shows the current connection state so you can quickly tell which mode is active.`,
      },
    ],
  },
]

function SectionCard({ section, isOpen, onToggle }) {
  return (
    <div className="card" style={{ marginBottom: 12, overflow: 'hidden' }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          background: isOpen ? 'var(--bg-raised)' : 'var(--bg-surface)',
          border: 'none',
          borderLeft: `3px solid ${section.color}`,
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          cursor: 'pointer',
          textAlign: 'left',
          transition: 'background 0.15s',
        }}
      >
        <span style={{ fontSize: 18, color: section.color, width: 28, flexShrink: 0, textAlign: 'center' }}>
          {section.icon}
        </span>
        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--txt)', flex: 1 }}>
          {section.title}
        </span>
        <span style={{ fontSize: 16, color: 'var(--txt-3)', transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}>
          ›
        </span>
      </button>

      {isOpen && (
        <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border)' }}>
          {section.content.map((item, i) => (
            <div key={i} style={{ marginTop: 20 }}>
              <h3 style={{
                fontSize: 13,
                fontWeight: 700,
                color: section.color,
                textTransform: 'uppercase',
                letterSpacing: '0.07em',
                marginBottom: 10,
                paddingBottom: 6,
                borderBottom: `1px solid var(--border)`,
              }}>
                {item.heading}
              </h3>
              <div style={{ fontSize: 13.5, color: 'var(--txt-2)', lineHeight: 1.75, whiteSpace: 'pre-line' }}>
                {item.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function AboutPage() {
  const [openSection, setOpenSection] = useState('overview')

  const toggle = (id) => setOpenSection(openSection === id ? null : id)

  return (
    <div>
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <div className="page-title">Help & Documentation</div>
          <div className="page-sub">Learn how to use each section of the MotorGuard console</div>
        </div>
      </div>

      {/* Quick reference colour legend */}
      <div className="card" style={{ marginBottom: 20, padding: '16px 20px' }}>
        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--txt-3)', marginBottom: 12 }}>
          ISA-101 Quick Reference
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {[
            { color: '#22c55e', label: 'NORMAL',   desc: 'Within safe operating limits' },
            { color: '#f59e0b', label: 'WARNING',  desc: 'Approaching a limit — investigate' },
            { color: '#ef4444', label: 'CRITICAL', desc: 'Fault detected — act immediately' },
            { color: '#0ea5e9', label: 'INFO',     desc: 'Informational / Neutral' },
            { color: '#64748b', label: 'UNKNOWN',  desc: 'No data or system starting up' },
          ].map(({ color, label, desc }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 36, height: 10, borderRadius: 5, background: color, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: '0.06em' }}>{label}</div>
                <div style={{ fontSize: 11, color: 'var(--txt-3)' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Accordion sections */}
      {SECTIONS.map((section) => (
        <SectionCard
          key={section.id}
          section={section}
          isOpen={openSection === section.id}
          onToggle={() => toggle(section.id)}
        />
      ))}

      <div style={{ marginTop: 24, padding: '16px 20px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', fontSize: 12, color: 'var(--txt-3)', lineHeight: 1.7 }}>
        <strong style={{ color: 'var(--txt-2)' }}>Standards referenced:</strong> ISA-101 (HMI design), ISA-18.2 (Alarm management), ISO 10816-3 (Vibration severity), IEC 60034 (Motor standards), NAMUR NE107 (Field device status).
      </div>
    </div>
  )
}
