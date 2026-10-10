import type { EventState } from '../types/event'

type EventDetailProps = {
  event: EventState
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

export function EventDetail({ event }: EventDetailProps) {
  return (
    <section className="detail-card">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Selected event</p>
          <h2>{event.info}</h2>
          <p className="event-id">ID: {event.event_id}</p>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-item">
          <span>Score</span>
          <strong>{event.score}</strong>
        </div>
        <div className="detail-item">
          <span>Date</span>
          <strong>{event.date}</strong>
        </div>
        <div className="detail-item">
          <span>Published</span>
          <strong>{event.published ? 'Yes' : 'No'}</strong>
        </div>
        <div className="detail-item">
          <span>Threat level</span>
          <strong>{event.threat_level_id}</strong>
        </div>
        <div className="detail-item">
          <span>Analysis</span>
          <strong>{event.analysis}</strong>
        </div>
        <div className="detail-item">
          <span>Attributes</span>
          <strong>{event.attribute_count}</strong>
        </div>
        <div className="detail-item">
          <span>Objects</span>
          <strong>{event.object_count}</strong>
        </div>
        <div className="detail-item detail-item-wide">
          <span>Fingerprint</span>
          <code>{event.fingerprint}</code>
        </div>
      </div>

      <div className="detail-section">
        <h3>Tags</h3>
        <TagList tags={event.tag_names} />
      </div>

      <div className="detail-section">
        <h3>Galaxy tags</h3>
        <TagList tags={event.galaxy_tag_names} />
      </div>
    </section>
  )
}
