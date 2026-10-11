import type { EventChange, EventState } from '../types/event'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type EventFilters = {
  fromDate?: string
  limit?: number
  minScore?: number
  published?: boolean
  toDate?: string
}

export async function fetchEvents(filters: EventFilters = {}): Promise<EventState[]> {
  const queryParams = new URLSearchParams()

  if (filters.limit !== undefined) {
    queryParams.set('limit', String(filters.limit))
  }

  if (filters.minScore !== undefined) {
    queryParams.set('min_score', String(filters.minScore))
  }

  if (filters.fromDate !== undefined && filters.fromDate !== '') {
    queryParams.set('from_date', filters.fromDate)
  }

  if (filters.toDate !== undefined && filters.toDate !== '') {
    queryParams.set('to_date', filters.toDate)
  }

  if (filters.published !== undefined) {
    queryParams.set('published', String(filters.published))
  }

  const queryString = queryParams.toString()
  const url = queryString === '' ? `${API_BASE_URL}/events` : `${API_BASE_URL}/events?${queryString}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.status}`)
  }

  return response.json()
}

export async function fetchEvent(event_id: string): Promise<EventState> {
  const response = await fetch(`${API_BASE_URL}/events/${event_id}`)

  if (!response.ok) {
    throw new Error(`Failed to fetch event ${event_id}: ${response.status}`)
  }

  return response.json()
}

export async function fetchEventChanges(event_id: string): Promise<EventChange[]> {
  const response = await fetch(`${API_BASE_URL}/events/${event_id}/changes`)

  if (!response.ok) {
    throw new Error(`Failed to fetch changes for event ${event_id}: ${response.status}`)
  }

  return response.json()
}
