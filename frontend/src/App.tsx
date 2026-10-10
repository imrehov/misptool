

import { useEffect, useState } from 'react'

import { fetchEvents } from './api/events'
import { EventTable } from './components/EventTable'
import type { EventState } from './types/event'
import './App.css'

function App() {
  const [events, setEvents] = useState<EventState[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadEvents() {
      try {
        const fetchedEvents = await fetchEvents()
        setEvents(fetchedEvents)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch events')
      } finally {
        setIsLoading(false)
      }
    }

    loadEvents()
  }, [])

  if (isLoading) {
    return <p>Loading events...</p>
  }

  if (error !== null) {
    return <p>{error}</p>
  }

  return (
    <main className="app">
      <header className="page-header">
        <div>
          <p className="eyebrow">Simple MISP UI</p>
          <h1>Event triage</h1>
        </div>
        <p className="event-count">{events.length} event(s)</p>
      </header>

      {events.length === 0 ? (
        <p>No events found.</p>
      ) : (
        <EventTable events={events} />
      )}
    </main>
  )
}

export default App
