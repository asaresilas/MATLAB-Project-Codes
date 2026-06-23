export const appConfig = {
  machineId: import.meta.env.VITE_MACHINE_ID || 'SCIM-01',
  appName:   import.meta.env.VITE_APP_NAME   || 'Induction Motor Digital Twin Console',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  wsUrl:      import.meta.env.VITE_WS_URL       || 'ws://127.0.0.1:8000/ws/dashboard',
  staleDataMs:      60000,
  reconnectBaseMs:  1000,
  reconnectMaxMs:  10000,
  trendWindows: [
    { key: '30s', label: '30 sec', maxPoints:  30 },
    { key: '5m',  label: '5 min',  maxPoints:  75 },
    { key: '1h',  label: '1 hr',   maxPoints: 120 },
  ],
  storageKeys: {
    session:  'dt_dashboard_session',
    settings: 'dt_dashboard_settings',
  },
}
