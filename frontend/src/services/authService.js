const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

/**
 * Check whether first-time setup is required.
 * Returns true if the backend has no accounts configured yet.
 */
export async function checkSetupRequired() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/setup-status`)
    if (!res.ok) return false
    const data = await res.json()
    return data.setup_required === true
  } catch {
    // CORS or network error — backend reachable but blocked, or truly down.
    // Default to false so the login page shows; user can click "First-time setup" link.
    return false
  }
}

/**
 * Submit the first-time setup form.
 * Creates the admin (and optionally engineer) account.
 */
export async function submitSetup({ adminUsername, adminPassword, adminFullName, engineerUsername, engineerPassword, engineerFullName }) {
  const body = new URLSearchParams({
    admin_username: adminUsername,
    admin_password: adminPassword,
    admin_fullname: adminFullName || 'System Administrator',
  })
  if (engineerUsername && engineerPassword) {
    body.append('engineer_username', engineerUsername)
    body.append('engineer_password', engineerPassword)
    body.append('engineer_fullname', engineerFullName || 'Maintenance Engineer')
  }

  const res = await fetch(`${API_BASE}/api/v1/auth/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(json.detail || `Setup failed (${res.status})`)
  return json
}

/**
 * Authenticate with the backend and return a session descriptor.
 * Fetches /auth/me after token grant to get the real role from the server.
 */
export async function authenticate(username, password) {
  let response
  try {
    response = await fetch(`${API_BASE}/api/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    })
  } catch {
    throw new Error('Cannot reach the backend server. Check that it is running on ' + API_BASE)
  }

  if (!response.ok) {
    if (response.status === 401) throw new Error('Invalid username or password.')
    if (response.status === 422) throw new Error('Username and password are required.')
    throw new Error(`Authentication failed (HTTP ${response.status}). Try again.`)
  }

  const data  = await response.json()
  const token = data.access_token

  /* Fetch the real profile so role is always server-authoritative */
  let role = 'operator', displayName = username
  try {
    const me = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (me.ok) {
      const profile = await me.json()
      role        = profile.role        || 'operator'
      displayName = profile.full_name   || profile.username || username
    }
  } catch { /* non-fatal — fall back to defaults */ }

  return { token, username, role, displayName }
}
