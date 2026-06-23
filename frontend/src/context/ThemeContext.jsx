/**
 * ThemeContext
 * Cycles through three display modes:
 *   dark  →  light  →  high-contrast  →  dark  …
 *
 * "high-contrast" satisfies ANSI/HFS 100 and WCAG 1.4.6 (Enhanced) for
 * critical-environment software operated under high-ambient-light conditions.
 */
import { createContext, useContext, useEffect, useState } from 'react'

const THEMES = ['dark', 'light', 'high-contrast']

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem('mg_theme')
      return THEMES.includes(stored) ? stored : 'dark'
    } catch {
      return 'dark'
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('mg_theme', theme) } catch {}
  }, [theme])

  /* Advance to next theme in cycle */
  const toggle = () =>
    setTheme((t) => THEMES[(THEMES.indexOf(t) + 1) % THEMES.length])

  /* Jump directly to a named theme */
  const setNamedTheme = (name) => {
    if (THEMES.includes(name)) setTheme(name)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggle, setNamedTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
