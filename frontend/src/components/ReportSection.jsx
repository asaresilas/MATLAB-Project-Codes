/**
 * ReportSection — Reusable section wrapper for the field inspection report.
 * Print-safe: adds a page-break-avoid hint and consistent heading style.
 */
export function ReportSection({ n, title, children, avoidBreak = false, className = '' }) {
  return (
    <div className={`rpt-section${avoidBreak ? ' rpt-avoid-break' : ''} ${className}`}>
      <div className="rpt-section-hd">
        <span className="rpt-section-n">{n}</span>
        {title}
      </div>
      {children}
    </div>
  )
}
