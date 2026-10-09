import json
from pathlib import Path
from typing import Any

from src.misptool.application.filters import EventStateFilters


class Storage:
    def __init__(self, path: str = "state.json") -> None:
        self.path = Path(path)
        self.events: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.events = {}
            return

        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.events = {}
            return

        events = data.get("events", {})
        self.events = events if isinstance(events, dict) else {}

    def save(self) -> None:
        data = {
            "events": self.events
        }

        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_event_state(self, event_id: str) -> dict[str, Any] | None:
        return self.events.get(str(event_id))

    def update_event_state(self, event_id: str, state: dict[str, Any]) -> None:
        self.events[str(event_id)] = state

    def list_event_states(self, filters: EventStateFilters) -> list[dict[str, Any]]:
        results = []

        for event_id in sorted(self.events.keys(), reverse=True):
            event = self.events[event_id]

            if filters.min_score is not None and event.get("score", 0) < filters.min_score:
                continue

            if filters.published is not None and event.get("published") != filters.published:
                continue

            event_date = event.get("date")

            if filters.from_date is not None and event_date < filters.from_date:
                continue

            if filters.to_date is not None and event_date > filters.to_date:
                continue

            results.append(event)

            if len(results) >= filters.limit:
                break

        return results

    def delete_event_state(self, event_id: str) -> None:
        self.events.pop(str(event_id), None)
