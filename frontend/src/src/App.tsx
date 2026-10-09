

import { useEffect, useState } from 'react'

import { fetchEvents } from './api/events'
import type { EventState } from './types/event'

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
    <main>
      <h1>MISP Events</h1>

      {events.length === 0 ? (
        <p>No events found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Score</th>
              <th>Date</th>
              <th>Info</th>
              <th>Published</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.event_id}>
                <td>{event.score}</td>
                <td>{event.date}</td>
                <td>{event.info}</td>
                <td>{event.published ? 'Yes' : 'No'}</td>
                <td>{event.tag_names.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}

export default App
