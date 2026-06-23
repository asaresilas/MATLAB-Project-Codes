export function StatusBadge({ label, tone = 'neutral' }) {
  return <span className={`status-badge tone-${tone}`}>{label}</span>
}
