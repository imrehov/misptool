const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiRequest(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers)
  if (options.method === 'POST') {
    headers.set('Content-Type', 'application/json')
    headers.set('X-CSRF-Protection', '1')
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options, headers, credentials: 'include', cache: 'no-store',
  })
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new Event('auth-expired'))
    }
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, typeof body?.detail === 'string'
      ? body.detail : `Request failed (${response.status})`)
  }
  return response
}
