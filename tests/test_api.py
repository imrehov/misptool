import pytest
from fastapi import HTTPException

from src.misptool.api.schemas import EventStateResponse
from src.misptool.api.routes import get_event_by_id, health, list_events


def fake_event(event_id: str, info: str, score: int) -> dict:
    return {
        "event_id": event_id,
        "info": info,
        "date": "2026-10-09",
        "timestamp": "1791504000",
        "publish_timestamp": "1791504100",
        "published": True,
        "threat_level_id": "2",
        "analysis": "1",
        "tag_names": ["tlp:white", "pytest"],
        "galaxy_tag_names": ["threat-actor:test"],
        "attribute_count": 12,
        "object_count": 3,
        "score": score,
        "fingerprint": f"fingerprint-{event_id}",
    }


class FakeEventStateRepository:
    def __init__(self):
        self.events = {
            "123": fake_event("123", "fake event 123", 7),
            "456": fake_event("456", "fake event 456", 4),
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

    result = list_events(repo=repo)

    assert result == [
        fake_event("123", "fake event 123", 7),
        fake_event("456", "fake event 456", 4),
    ]


def test_get_event_by_id_returns_fake_event():
    repo = FakeEventStateRepository()

    result = get_event_by_id(event_id="123", repo=repo)

    assert result == fake_event("123", "fake event 123", 7)


def test_get_event_by_id_returns_404_for_missing_event():
    repo = FakeEventStateRepository()

    with pytest.raises(HTTPException) as error:
        get_event_by_id(event_id="missing", repo=repo)

    assert error.value.status_code == 404
    assert error.value.detail == "wrong event id: missing"


def test_list_events_response_shape_matches_schema():
    repo = FakeEventStateRepository()

    result = list_events(repo=repo)
    validated_events = [EventStateResponse.model_validate(event) for event in result]

    assert len(validated_events) == 2
    assert validated_events[0].event_id == "123"
    assert validated_events[0].info == "fake event 123"
    assert validated_events[0].score == 7
    assert validated_events[0].tag_names == ["tlp:white", "pytest"]


def test_get_event_by_id_response_shape_matches_schema():
    repo = FakeEventStateRepository()

    result = get_event_by_id(event_id="123", repo=repo)
    validated_event = EventStateResponse.model_validate(result)

    assert validated_event.event_id == "123"
    assert validated_event.info == "fake event 123"
    assert validated_event.score == 7
    assert validated_event.fingerprint == "fingerprint-123"
