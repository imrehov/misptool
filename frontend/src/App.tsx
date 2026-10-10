

import { useCallback, useEffect, useState } from 'react'

import { fetchEvents } from './api/events'
import { EventTable } from './components/EventTable'
import type { EventState } from './types/event'
import './App.css'

const AUTO_REFRESH_INTERVAL_MS = 60_000
const AUTO_REFRESH_INTERVAL_SECONDS = AUTO_REFRESH_INTERVAL_MS / 1000
type Theme = 'light' | 'dark'

function getInitialTheme(): Theme {
  const savedTheme = window.localStorage.getItem('theme')

  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme
  }

  return 'light'
}

function App() {
  const [events, setEvents] = useState<EventState[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(
    AUTO_REFRESH_INTERVAL_SECONDS,
  )
  const [error, setError] = useState<string | null>(null)
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  const loadEvents = useCallback(async ({ showInitialLoading = false } = {}) => {
    if (showInitialLoading) {
      setIsLoading(true)
    } else {
      setIsRefreshing(true)
    }

    setError(null)

    try {
      const fetchedEvents = await fetchEvents()
      setEvents(fetchedEvents)
      setSecondsUntilRefresh(AUTO_REFRESH_INTERVAL_SECONDS)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadEvents({ showInitialLoading: true })
  }, [loadEvents])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    const refreshIntervalId = window.setInterval(() => {
      loadEvents()
    }, AUTO_REFRESH_INTERVAL_MS)

    const countdownIntervalId = window.setInterval(() => {
      setSecondsUntilRefresh((currentSeconds) => {
        if (currentSeconds <= 1) {
          return AUTO_REFRESH_INTERVAL_SECONDS
        }

        return currentSeconds - 1
      })
    }, 1000)

    return () => {
      window.clearInterval(refreshIntervalId)
      window.clearInterval(countdownIntervalId)
    }
  }, [loadEvents])

  if (isLoading) {
    return <p>Loading events...</p>
  }

  return (
    <main className="app">
      <header className="page-header">
        <div>
          <p className="eyebrow">Simple MISP UI</p>
          <h1>Event triage</h1>
        </div>
        <div className="header-actions">
          <div className="refresh-status">
            <p className="event-count">{events.length} event(s)</p>
            <p className="refresh-countdown">
              Next auto refresh in {secondsUntilRefresh}s
            </p>
          </div>
          <button
            className="refresh-button"
            disabled={isRefreshing}
            onClick={() => loadEvents()}
            type="button"
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
            className="theme-toggle"
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
            type="button"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      {error !== null && <p className="error-message">{error}</p>}

      {events.length === 0 ? (
        <p>No events found.</p>
      ) : (
        <EventTable events={events} />
      )}
    </main>
  )
}

export default App
