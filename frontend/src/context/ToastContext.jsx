import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

const ToastContext = createContext(null)

let _toastId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id))
  }, [])

  const push = useCallback(({ title, message, type = 'ok', duration = 4000 }) => {
    _toastId += 1
    const id = _toastId
    setToasts((t) => [...t.slice(-4), { id, title, message, type }])
    if (duration > 0) setTimeout(() => dismiss(id), duration)
    return id
  }, [dismiss])

  const root = document.getElementById('toast-root')

  return (
    <ToastContext.Provider value={{ push, dismiss }}>
      {children}
      {root && createPortal(
        <>{toasts.map((t) => (
          <Toast key={t.id} {...t} onDismiss={() => dismiss(t.id)} />
        ))}</>,
        root
      )}
    </ToastContext.Provider>
  )
}

function Toast({ id, title, message, type, onDismiss }) {
  const icon = type === 'err' ? '⛔' : type === 'warn' ? '⚠️' : type === 'ok' ? '✅' : 'ℹ️'
  return (
    <div className={`toast ${type}`} onClick={onDismiss} role="alert">
      <span className="toast-icon">{icon}</span>
      <div className="toast-body">
        <div className="toast-title">{title}</div>
        {message && <div className="toast-msg">{message}</div>}
      </div>
      <button className="toast-close" onClick={(e) => { e.stopPropagation(); onDismiss() }}>×</button>
    </div>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
