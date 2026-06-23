import { useEffect } from 'react'

const SHORTCUTS = [
  { section: 'Navigation' },
  { keys: ['D'],         desc: 'Go to Dashboard'    },
  { keys: ['S'],         desc: 'Go to Live Sensors'  },
  { keys: ['T'],         desc: 'Go to Trends'        },
  { keys: ['A'],         desc: 'Go to Alarms'        },
  { keys: ['G'],         desc: 'Go to Settings'      },
  { keys: ['H'],         desc: 'Go to Help / About'  },

  { section: 'Display' },
  { keys: ['L'],         desc: 'Cycle theme: dark → light → high-contrast' },
  { keys: ['F11'],       desc: 'Enter / exit fullscreen'                   },
  { keys: ['?'],         desc: 'Show this shortcuts panel'                 },

  { section: 'Alarms' },
  { keys: ['M'],         desc: 'Toggle alarm sound mute'     },
  { keys: ['A'],         desc: 'Go to Alarm Center'          },

  { section: 'Actions' },
  { keys: ['Esc'],       desc: 'Close any open panel'        },
  { keys: ['R'],         desc: 'Refresh sensor data'         },
]

export function KeyboardShortcuts({ onClose }) {
  /* Close on Escape */
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div className="shortcuts-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Keyboard shortcuts">
      <div className="shortcuts-panel" onClick={(e) => e.stopPropagation()}>
        <div className="shortcuts-header">
          <span>Keyboard Shortcuts</span>
          <button className="shortcuts-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="shortcuts-body">
          {SHORTCUTS.map((item, i) =>
            item.section ? (
              <div key={i} className="shortcuts-section-title">{item.section}</div>
            ) : (
              <div key={i} className="shortcuts-row">
                <div className="shortcuts-keys">
                  {item.keys.map((k) => <kbd key={k}>{k}</kbd>)}
                </div>
                <span className="shortcuts-desc">{item.desc}</span>
              </div>
            )
          )}
        </div>

        <div className="shortcuts-footer">
          Press <kbd>Esc</kbd> or click outside to close
        </div>
      </div>
    </div>
  )
}
