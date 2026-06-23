import { validateDashboardMessage } from '../utils/validation.js'

export function createDashboardSocketClient({ url, onStateChange, onMessage, onError, reconnectBaseMs, reconnectMaxMs }) {
  let socket = null
  let reconnectAttempts = 0
  let reconnectTimer = null
  let manuallyClosed = false

  const clearReconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  const scheduleReconnect = () => {
    clearReconnect()
    const delay = Math.min(reconnectBaseMs * (2 ** reconnectAttempts), reconnectMaxMs)
    reconnectAttempts += 1
    reconnectTimer = setTimeout(() => {
      onStateChange?.('connecting')
      connect()
    }, delay)
  }

  const connect = () => {
    try {
      socket = new WebSocket(url)
      onStateChange?.('connecting')
      socket.onopen = () => {
        reconnectAttempts = 0
        onStateChange?.('connected')
      }
      socket.onmessage = (event) => {
        let payload
        try {
          payload = JSON.parse(event.data)
        } catch (error) {
          onError?.(`Malformed JSON payload: ${error.message}`)
          return
        }
        const validation = validateDashboardMessage(payload)
        if (!validation.ok) {
          onError?.(validation.error)
          return
        }
        onMessage?.(payload)
      }
      socket.onerror = () => onError?.('WebSocket transport error')
      socket.onclose = () => {
        if (manuallyClosed) return
        onStateChange?.('disconnected')
        scheduleReconnect()
      }
    } catch (error) {
      onStateChange?.('backend_error')
      onError?.(error.message)
      scheduleReconnect()
    }
  }

  return {
    connect,
    close: () => {
      manuallyClosed = true
      clearReconnect()
      socket?.close()
    },
  }
}
