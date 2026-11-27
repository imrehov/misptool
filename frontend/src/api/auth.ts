import { apiRequest } from './client'

export async function checkSession(): Promise<void> {
  await apiRequest('/auth/session')
}

export async function login(password: string): Promise<void> {
  await apiRequest('/auth/login', {
    method: 'POST', body: JSON.stringify({ password }),
  })
}

export async function logout(): Promise<void> {
  await apiRequest('/auth/logout', { method: 'POST' })
}
