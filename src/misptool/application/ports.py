# src/misptool/application/ports.py
from typing import Any, Protocol

from src.misptool.application.filters import EventStateFilters


class EventStateRepository(Protocol):
    def get_event_state(self, event_id: str) -> dict[str, Any] | None:
        ...

    def update_event_state(self, event_id: str, state: dict[str, Any]) -> None:
        ...

    def list_event_states(self, filters: EventStateFilters) -> list[dict[str, Any]]:
        ...

    def save(self) -> None:
        ...

    def record_event_change(
        self,
        event_id: str,
        change_type: str,
        old_state: dict | None,
        new_state: dict,
        change_summary: list[str],
    ) -> None:
        ...

    def list_event_changes(event_id: str) -> list[dict]:
        ...

class MispEventSource(Protocol):
    def fetch_events(self, lookback_minutes: int) -> list[dict[str, Any]]:
        ...

class EventNotifier(Protocol):
    def notify_console(self, summary: dict[str, Any]) -> None:
        ...

    def notify_discord(self, summary: dict[str, Any]) -> None:
        ...
