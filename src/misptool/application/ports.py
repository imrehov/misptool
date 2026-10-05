# src/misptool/application/ports.py
from typing import Any, Protocol


class EventStateRepository(Protocol):
    def get_event_state(self, event_id: str) -> dict[str, Any] | None:
        ...

    def update_event_state(self, event_id: str, state: dict[str, Any]) -> None:
        ...

    def save(self) -> None:
        ...

class MispEventSource(Protocol):
    def fetch_events(self, lookback_minutes: int) -> list[dict[str, Any]]:
        ...