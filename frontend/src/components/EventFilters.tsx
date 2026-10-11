import type { EventFilters as ApiEventFilters } from '../api/events'

export type EventFilterFormState = {
  fromDate: string
  limit: number
  minScore: string
  published: 'all' | 'true' | 'false'
  search: string
  toDate: string
}

type EventFiltersProps = {
  filters: EventFilterFormState
  onChange: (filters: EventFilterFormState) => void
  onReset: () => void
  onSubmit: () => void
}

export function toApiFilters(filters: EventFilterFormState): ApiEventFilters {
  return {
    fromDate: filters.fromDate,
    limit: filters.limit,
    minScore: filters.minScore === '' ? undefined : Number(filters.minScore),
    published:
      filters.published === 'all' ? undefined : filters.published === 'true',
    toDate: filters.toDate,
  }
}

export function EventFilters({
  filters,
  onChange,
  onReset,
  onSubmit,
}: EventFiltersProps) {
  return (
    <form
      className="filters-card"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <label>
        <span>Search</span>
        <input
          onChange={(event) => onChange({ ...filters, search: event.target.value })}
          placeholder="Title, event ID, tag..."
          type="search"
          value={filters.search}
        />
      </label>

      <label>
        <span>Min score</span>
        <input
          min="0"
          onChange={(event) => onChange({ ...filters, minScore: event.target.value })}
          placeholder="Any"
          type="number"
          value={filters.minScore}
        />
      </label>

      <label>
        <span>Published</span>
        <select
          onChange={(event) =>
            onChange({
              ...filters,
              published: event.target.value as EventFilterFormState['published'],
            })
          }
          value={filters.published}
        >
          <option value="all">All</option>
          <option value="true">Published</option>
          <option value="false">Unpublished</option>
        </select>
      </label>

      <label>
        <span>From date</span>
        <input
          onChange={(event) => onChange({ ...filters, fromDate: event.target.value })}
          type="date"
          value={filters.fromDate}
        />
      </label>

      <label>
        <span>To date</span>
        <input
          onChange={(event) => onChange({ ...filters, toDate: event.target.value })}
          type="date"
          value={filters.toDate}
        />
      </label>

      <label>
        <span>Limit</span>
        <input
          min="1"
          onChange={(event) =>
            onChange({ ...filters, limit: Number(event.target.value) })
          }
          type="number"
          value={filters.limit}
        />
      </label>

      <div className="filter-actions">
        <button className="refresh-button" type="submit">
          Apply
        </button>
        <button className="secondary-button" onClick={onReset} type="button">
          Reset
        </button>
      </div>
    </form>
  )
}
