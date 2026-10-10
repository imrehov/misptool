import type { EventState } from '../types/event'

type EventTableProps = {
  events: EventState[]
}

const MISP_BASE_URL = import.meta.env.VITE_MISP_BASE_URL ?? 'http://localhost'

function buildMispEventUrl(eventId: string): string {
  return `${MISP_BASE_URL.replace(/\/$/, '')}/events/view/${eventId}`
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

export function EventTable({ events }: EventTableProps) {
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
            <tr key={event.event_id}>
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
                  <a href={buildMispEventUrl(event.event_id)} rel="noreferrer" target="_blank">
                    Open in MISP
                  </a>
                  <a href={`/events/${event.event_id}`}>Details later</a>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
