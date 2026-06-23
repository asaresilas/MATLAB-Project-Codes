export function MotorSchematic({ healthState = 'unknown' }) {
  const stateClass = {
    normal:   'ok',
    warning:  'warn',
    critical: 'crit',
  }[healthState?.toLowerCase()] || ''

  const glowColor = {
    ok:   '#22c55e',
    warn: '#f59e0b',
    crit: '#ef4444',
  }[stateClass] || '#0ea5e9'

  return (
    <div className={`motor-schematic-wrap ${stateClass}`}>
      <svg viewBox="0 0 420 220" xmlns="http://www.w3.org/2000/svg" aria-label="Induction motor cross-section schematic">
        <defs>
          <radialGradient id="motorGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={glowColor} stopOpacity="0.18" />
            <stop offset="100%" stopColor={glowColor} stopOpacity="0" />
          </radialGradient>
          <linearGradient id="housingGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2a3347" />
            <stop offset="100%" stopColor="#1e2535" />
          </linearGradient>
          <linearGradient id="statorGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#334155" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>
          <linearGradient id="rotorGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#0284c7" stopOpacity="0.5" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Ambient glow behind motor */}
        <ellipse cx="210" cy="110" rx="130" ry="90" fill="url(#motorGlow)" />

        {/* Motor housing (outer casing) */}
        <rect x="60" y="45" width="300" height="130" rx="18" fill="url(#housingGrad)" stroke="#3d4f6e" strokeWidth="2" />

        {/* Cooling fins - top */}
        {[80,104,128,152,176,200,224,248,272,296,320].map((x) => (
          <rect key={`ft${x}`} x={x} y="30" width="10" height="16" rx="2" fill="#2a3347" stroke="#3d4f6e" strokeWidth="1" />
        ))}

        {/* Cooling fins - bottom */}
        {[80,104,128,152,176,200,224,248,272,296,320].map((x) => (
          <rect key={`fb${x}`} x={x} y="174" width="10" height="16" rx="2" fill="#2a3347" stroke="#3d4f6e" strokeWidth="1" />
        ))}

        {/* Stator body */}
        <rect x="80" y="63" width="260" height="94" rx="8" fill="url(#statorGrad)" stroke="#475569" strokeWidth="1.5" />

        {/* Stator windings - left side */}
        {[72,88,104].map((y) => (
          <rect key={`wl${y}`} x="86" y={y} width="24" height="10" rx="3" fill="#f59e0b" opacity="0.7" />
        ))}

        {/* Stator windings - right side */}
        {[72,88,104].map((y) => (
          <rect key={`wr${y}`} x="310" y={y} width="24" height="10" rx="3" fill="#f59e0b" opacity="0.7" />
        ))}

        {/* Stator windings - top */}
        {[130,158,186,214,242,270].map((x) => (
          <rect key={`wt${x}`} x={x} y="66" width="10" height="20" rx="3" fill="#f59e0b" opacity="0.7" />
        ))}

        {/* Stator windings - bottom */}
        {[130,158,186,214,242,270].map((x) => (
          <rect key={`wb${x}`} x={x} y="134" width="10" height="20" rx="3" fill="#f59e0b" opacity="0.7" />
        ))}

        {/* Air gap */}
        <ellipse cx="210" cy="110" rx="70" ry="46" fill="none" stroke="#3d4f6e" strokeWidth="1" strokeDasharray="4 3" />

        {/* Rotor */}
        <ellipse cx="210" cy="110" rx="60" ry="40" fill="url(#rotorGrad)" stroke={glowColor} strokeWidth="1.5" filter="url(#glow)" opacity="0.9" />

        {/* Rotor bars */}
        {Array.from({length: 10}).map((_, i) => {
          const angle = (i / 10) * Math.PI * 2
          const rx = 48, ry = 30
          const x = 210 + rx * Math.cos(angle)
          const y = 110 + ry * Math.sin(angle)
          return (
            <ellipse key={`rb${i}`} cx={x} cy={y} rx="5" ry="3"
              fill="#0ea5e9" opacity="0.6"
              transform={`rotate(${(angle * 180 / Math.PI)},${x},${y})`}
            />
          )
        })}

        {/* Shaft */}
        <rect x="20" y="105" width="40" height="10" rx="5" fill="#475569" stroke="#64748b" strokeWidth="1.5" />
        <rect x="360" y="105" width="40" height="10" rx="5" fill="#475569" stroke="#64748b" strokeWidth="1.5" />

        {/* Bearings */}
        <circle cx="78" cy="110" r="10" fill="none" stroke="#94a3b8" strokeWidth="2.5" />
        <circle cx="78" cy="110" r="4" fill="#64748b" />
        <circle cx="342" cy="110" r="10" fill="none" stroke="#94a3b8" strokeWidth="2.5" />
        <circle cx="342" cy="110" r="4" fill="#64748b" />

        {/* Terminal box */}
        <rect x="170" y="15" width="80" height="20" rx="4" fill="#1e2535" stroke="#3d4f6e" strokeWidth="1.5" />
        <circle cx="190" cy="25" r="4" fill="#ef4444" />
        <circle cx="210" cy="25" r="4" fill="#f59e0b" />
        <circle cx="230" cy="25" r="4" fill="#22c55e" />

        {/* Health state indicator overlay */}
        <ellipse cx="210" cy="110" rx="62" ry="42"
          fill="none"
          stroke={glowColor}
          strokeWidth="2"
          opacity="0.5"
          strokeDasharray={stateClass === 'crit' ? '6 3' : 'none'}
        >
          {stateClass === 'crit' && (
            <animateTransform attributeName="transform" type="rotate" from="0 210 110" to="360 210 110" dur="4s" repeatCount="indefinite" />
          )}
        </ellipse>

        {/* Labels */}
        <text x="210" y="205" textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="Inter, sans-serif" fontWeight="600" letterSpacing="1">
          SQUIRREL CAGE INDUCTION MOTOR
        </text>

        <text x="78" y="135" textAnchor="middle" fill="#64748b" fontSize="8.5" fontFamily="Inter, sans-serif">BEARING</text>
        <text x="342" y="135" textAnchor="middle" fill="#64748b" fontSize="8.5" fontFamily="Inter, sans-serif">BEARING</text>
        <text x="38" y="120" textAnchor="middle" fill="#64748b" fontSize="8.5" fontFamily="Inter, sans-serif">SHAFT</text>
      </svg>
    </div>
  )
}
