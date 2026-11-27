import type { EventChange, EventState } from '../types/event'
import { apiRequest } from './client'

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
  const url = queryString === '' ? '/events' : `/events?${queryString}`

  const response = await apiRequest(url)

  return response.json()
}

export async function fetchEvent(event_id: string): Promise<EventState> {
  const response = await apiRequest(`/events/${event_id}`)

  return response.json()
}

export async function fetchEventChanges(event_id: string): Promise<EventChange[]> {
  const response = await apiRequest(`/events/${event_id}/changes`)

  return response.json()
}
