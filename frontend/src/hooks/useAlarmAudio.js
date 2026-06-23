/**
 * useAlarmAudio
 * Generates audible alarm tones via the Web Audio API whenever the machine
 * health state is CRITICAL. Tone repeats every 8 s until the state clears
 * or the user mutes. Mute preference is persisted in localStorage.
 *
 * ISA-18.2 §12 requires audible indication for unacknowledged critical alarms.
 */
import { useEffect, useRef, useState } from 'react'

export function useAlarmAudio(healthState) {
  const [muted, setMuted] = useState(() => {
    try { return localStorage.getItem('mg_alarm_mute') === 'true' } catch { return false }
  })

  const ctxRef      = useRef(null)
  const intervalRef = useRef(null)

  /* Lazy AudioContext creation (must be after user interaction on some browsers) */
  function getCtx() {
    if (!ctxRef.current) {
      ctxRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (ctxRef.current.state === 'suspended') ctxRef.current.resume()
    return ctxRef.current
  }

  /* Two-burst tone: 880 Hz → 1100 Hz, 200 ms each */
  function playTone() {
    try {
      const ctx = getCtx()
      const now = ctx.currentTime

      ;[880, 1100].forEach((freq, i) => {
        const osc  = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.connect(gain)
        gain.connect(ctx.destination)

        osc.type          = 'sine'
        osc.frequency.value = freq

        const t0 = now + i * 0.28
        gain.gain.setValueAtTime(0, t0)
        gain.gain.linearRampToValueAtTime(0.18, t0 + 0.02)
        gain.gain.exponentialRampToValueAtTime(0.001, t0 + 0.22)

        osc.start(t0)
        osc.stop(t0 + 0.24)
      })
    } catch (err) {
      /* AudioContext unavailable (unit tests, non-secure contexts) */
      console.warn('[AlarmAudio] Web Audio API unavailable:', err)
    }
  }

  useEffect(() => {
    const isCritical = (healthState || '').toUpperCase() === 'CRITICAL'

    /* Stop any running interval */
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (!isCritical || muted) return

    /* Fire immediately then repeat every 8 s */
    playTone()
    intervalRef.current = setInterval(playTone, 8000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [healthState, muted])   // eslint-disable-line react-hooks/exhaustive-deps

  const toggleMute = () => {
    setMuted((prev) => {
      const next = !prev
      try { localStorage.setItem('mg_alarm_mute', String(next)) } catch {}
      return next
    })
  }

  return { muted, toggleMute }
}
