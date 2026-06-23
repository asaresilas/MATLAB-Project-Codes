import { appConfig } from '../config/appConfig.js'

const readStorage = (key, fallback) => {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (err) {
    console.warn('[storage] Failed to read key', key, '—', err.message)
    return fallback
  }
}

const writeStorage = (key, value) => {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch (err) {
    console.warn('[storage] Failed to write key', key, '—', err.message, '(localStorage may be full or disabled)')
  }
}

export const sessionService = {
  loadSession:  ()        => readStorage(appConfig.storageKeys.session, null),
  saveSession:  (session) => writeStorage(appConfig.storageKeys.session, session),
  clearSession: ()        => {
    try {
      window.localStorage.removeItem(appConfig.storageKeys.session)
    } catch (err) {
      console.warn('[storage] Failed to clear session —', err.message)
    }
  },
}

export const settingsService = {
  loadSettings: (defaults)  => ({ ...defaults, ...readStorage(appConfig.storageKeys.settings, {}) }),
  saveSettings: (settings)  => writeStorage(appConfig.storageKeys.settings, settings),
}
