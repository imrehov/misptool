import type { EventState } from '../types/event'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function fetchEvents(): Promise<EventState[]> {
  const response = await fetch(`${API_BASE_URL}/events`)

  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.status}`)
  }

  return response.json()
}
