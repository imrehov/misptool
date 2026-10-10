import { Fragment } from 'react'

import type { EventState } from '../types/event'
import { EventDetail } from './EventDetail'

type EventTableProps = {
  events: EventState[]
  isDetailLoading: boolean
  onCloseDetail: () => void
  onSelectEvent: (eventId: string) => void
  selectedEvent: EventState | null
  selectedEventId: string | null
}

function scoreClassName(score: number): string {
  if (score >= 8) {
    return 'score score-critical'
  }

  if (score >= 5) {
    return 'score score-high'
  }

  return 'score'
}

function TagList({ tags }: { tags: string[] }) {
  if (tags.length === 0) {
    return <span className="muted">None</span>
  }

  return (
    <div className="tag-list">
      {tags.map((tag) => (
        <span className="tag" key={tag}>
          {tag}
        </span>
      ))}
    </div>
  )
}

export function EventTable({
  events,
  isDetailLoading,
  onCloseDetail,
  onSelectEvent,
  selectedEvent,
  selectedEventId,
}: EventTableProps) {
  return (
    <div className="table-wrapper">
      <table className="event-table">
        <thead>
          <tr>
            <th>Score</th>
            <th>Date</th>
            <th>Event</th>
            <th>Published</th>
            <th>Attributes</th>
            <th>Objects</th>
            <th>Tags</th>
            <th>Galaxies</th>
            <th>Links</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <Fragment key={event.event_id}>
              <tr>
                <td>
                  <span className={scoreClassName(event.score)}>{event.score}</span>
                </td>
                <td>{event.date}</td>
                <td>
                  <div className="event-title">{event.info}</div>
                  <div className="event-id">ID: {event.event_id}</div>
                </td>
                <td>
                  <span className={event.published ? 'status published' : 'status unpublished'}>
                    {event.published ? 'Published' : 'Unpublished'}
                  </span>
                </td>
                <td>{event.attribute_count}</td>
                <td>{event.object_count}</td>
                <td>
                  <TagList tags={event.tag_names} />
                </td>
                <td>
                  <TagList tags={event.galaxy_tag_names} />
                </td>
                <td>
                  <div className="link-list">
                    <a href={event.misp_event_url} rel="noreferrer" target="_blank">
                      Open in MISP
                    </a>
                    {selectedEventId === event.event_id ? (
                      <button className="link-button" onClick={onCloseDetail} type="button">
                        Close
                      </button>
                    ) : (
                      <button
                        className="link-button"
                        onClick={() => onSelectEvent(event.event_id)}
                        type="button"
                      >
                        Details
                      </button>
                    )}
                  </div>
                </td>
              </tr>

              {isDetailLoading && selectedEventId === event.event_id && (
                <tr className="detail-row">
                  <td colSpan={9}>
                    <p className="loading-message">Loading event detail...</p>
                  </td>
                </tr>
              )}

              {selectedEvent?.event_id === event.event_id && (
                <tr className="detail-row">
                  <td colSpan={9}>
                    <EventDetail event={selectedEvent} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
