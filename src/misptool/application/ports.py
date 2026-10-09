# src/misptool/application/ports.py
from typing import Any, Protocol


class EventStateRepository(Protocol):
    def get_event_state(self, event_id: str) -> dict[str, Any] | None:
        ...

    def update_event_state(self, event_id: str, state: dict[str, Any]) -> None:
        ...

    def list_event_states(self, limit: int = 50) -> list[dict[str, Any]]:
        ...

    def save(self) -> None:
        ...

class MispEventSource(Protocol):
    def fetch_events(self, lookback_minutes: int) -> list[dict[str, Any]]:
        ...

class EventNotifier(Protocol):
    def notify_console(self, summary: dict[str, Any]) -> None:
        ...

    def notify_discord(self, summary: dict[str, Any]) -> None:
        ...
