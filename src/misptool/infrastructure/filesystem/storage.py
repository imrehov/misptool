import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.misptool.application.filters import EventStateFilters


class Storage:
    def __init__(self, path: str = "state.json") -> None:
        self.path = Path(path)
        self.events: dict[str, dict[str, Any]] = {}
        self.changes: dict[str, list[dict[str, Any]]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.events = {}
            self.changes = {}
            return

        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.events = {}
            self.changes = {}
            return

        events = data.get("events", {})
        self.events = events if isinstance(events, dict) else {}

        changes = data.get("changes", {})
        self.changes = changes if isinstance(changes, dict) else {}

    def save(self) -> None:
        data = {
            "events": self.events,
            "changes": self.changes,
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

    def record_event_change(
        self,
        event_id: str,
        change_type: str,
        old_state: dict[str, Any] | None,
        new_state: dict[str, Any],
        change_summary: list[str],
    ) -> None:
        event_id = str(event_id)
        event_changes = self.changes.setdefault(event_id, [])

        event_changes.append({
            "event_id": event_id,
            "change_type": change_type,
            "old_fingerprint": None if old_state is None else old_state.get("fingerprint"),
            "new_fingerprint": new_state["fingerprint"],
            "old_score": None if old_state is None else old_state.get("score"),
            "new_score": new_state["score"],
            "change_summary": change_summary,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        })

    def list_event_changes(self, event_id: str) -> list[dict[str, Any]]:
        return self.changes.get(str(event_id), [])

    def delete_event_state(self, event_id: str) -> None:
        self.events.pop(str(event_id), None)
