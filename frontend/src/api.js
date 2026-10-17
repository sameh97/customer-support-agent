// Thin wrapper around the FastAPI endpoints in src/api.py.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const getInfo = () => request('/info')

export const sendMessage = (message, sessionId) =>
  request('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  })

export const answerConfirmation = (sessionId, approved) =>
  request('/chat/confirm', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, approved }),
  })
