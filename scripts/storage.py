import json
from pathlib import Path
from typing import Any


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

    def delete_event_state(self, event_id: str) -> None:
        self.events.pop(str(event_id), None)