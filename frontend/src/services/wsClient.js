import { validateDashboardMessage } from '../utils/validation.js'

// Maximum silence before treating the connection as stale and reconnecting.
// The backend sends a heartbeat ping every ~30 s; 45 s gives one missed ping
// before we act, avoiding false reconnects on transient slow messages.
const HEARTBEAT_TIMEOUT_MS = 45_000

export function createDashboardSocketClient({ url, onStateChange, onMessage, onError, reconnectBaseMs, reconnectMaxMs }) {
  let socket = null
  let reconnectAttempts = 0
  let reconnectTimer = null
  let heartbeatTimer = null
  let manuallyClosed = false
  let lastMessageTimestamp = 0   // epoch ms of last received message (any type)

  const clearReconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  const clearHeartbeat = () => {
    if (heartbeatTimer) {
      clearTimeout(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // Arm a watchdog: if no message arrives within HEARTBEAT_TIMEOUT_MS we
  // force-close the socket so the normal onclose → scheduleReconnect path fires.
  const resetHeartbeat = () => {
    clearHeartbeat()
    heartbeatTimer = setTimeout(() => {
      if (!manuallyClosed && socket) {
        onStateChange?.('reconnecting')
        onError?.('Heartbeat timeout — no message from server in 45 s. Reconnecting…')
        socket.close()
      }
    }, HEARTBEAT_TIMEOUT_MS)
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
        resetHeartbeat()
      }
      socket.onmessage = (event) => {
        lastMessageTimestamp = Date.now()
        resetHeartbeat()   // reset watchdog on every received message

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
        // Pass the original parsed payload; the controller filters by payload.type
        onMessage?.(payload)
      }
      socket.onerror = () => onError?.('WebSocket transport error')
      socket.onclose = () => {
        clearHeartbeat()
        if (manuallyClosed) return
        onStateChange?.('reconnecting')
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
    /** Returns milliseconds since the last message was received (0 if never). */
    getDataAgeMs: () => lastMessageTimestamp > 0 ? Date.now() - lastMessageTimestamp : 0,
    close: () => {
      manuallyClosed = true
      clearReconnect()
      clearHeartbeat()
      socket?.close()
    },
  }
}
