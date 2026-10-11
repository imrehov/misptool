import { useEffect, useState } from 'react'

import { fetchEventChanges } from '../api/events'
import type { EventChange } from '../types/event'

type EventChangeHistoryProps = {
  eventId: string
}

function formatObservedAt(value: string) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}

export function EventChangeHistory({ eventId }: EventChangeHistoryProps) {
  const [changes, setChanges] = useState<EventChange[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let ignore = false

    async function loadChanges() {
      setError(null)
      setIsLoading(true)

      try {
        const nextChanges = await fetchEventChanges(eventId)

        if (!ignore) {
          setChanges(nextChanges)
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : 'Failed to fetch event changes')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    loadChanges()

    return () => {
      ignore = true
    }
  }, [eventId])

  return (
    <div className="detail-section">
      <h3>Recent changes</h3>

      {isLoading && <p className="muted">Loading changes…</p>}

      {error !== null && <p className="history-error">{error}</p>}

      {!isLoading && error === null && changes.length === 0 && (
        <p className="muted">No recorded changes yet.</p>
      )}

      {!isLoading && error === null && changes.length > 0 && (
        <ol className="change-history">
          {changes.map((change, index) => (
            <li className="change-history-item" key={change.id ?? `${change.observed_at}-${index}`}>
              <div className="change-history-meta">
                <span className="change-type">{change.change_type}</span>
                <span>{formatObservedAt(change.observed_at)}</span>
              </div>

              <ul className="change-summary">
                {change.change_summary.map((summary) => (
                  <li key={summary}>{summary}</li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
