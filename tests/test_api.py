import pytest
from fastapi import HTTPException

from src.misptool.api.routes import get_event_by_id, health, list_events


class FakeEventStateRepository:
    def __init__(self):
        self.events = {
            "123": {
                "event_id": "123",
                "info": "fake event 123",
                "score": 7,
            },
            "456": {
                "event_id": "456",
                "info": "fake event 456",
                "score": 4,
            },
        }

    def get_event_state(self, event_id: str) -> dict | None:
        return self.events.get(event_id)

    def list_event_states(self, limit: int = 50) -> list[dict]:
        return list(self.events.values())[:limit]

    def update_event_state(self, event_id: str, state: dict) -> None:
        self.events[event_id] = state

    def save(self) -> None:
        pass


def test_health_returns_ok():
    assert health() == {"status": "ok"}


def test_list_events_returns_fake_events():
    repo = FakeEventStateRepository()

    assert list_events(repo=repo) == [
        {
            "event_id": "123",
            "info": "fake event 123",
            "score": 7,
        },
        {
            "event_id": "456",
            "info": "fake event 456",
            "score": 4,
        },
    ]


def test_get_event_by_id_returns_fake_event():
    repo = FakeEventStateRepository()

    assert get_event_by_id(event_id="123", repo=repo) == {
        "event_id": "123",
        "info": "fake event 123",
        "score": 7,
    }


def test_get_event_by_id_returns_404_for_missing_event():
    repo = FakeEventStateRepository()

    with pytest.raises(HTTPException) as error:
        get_event_by_id(event_id="missing", repo=repo)

    assert error.value.status_code == 404
    assert error.value.detail == "wrong event id: missing"
