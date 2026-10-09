import os

import pytest

from src.misptool.infrastructure.db.models import Base
from src.misptool.infrastructure.db.session import DbSession
from src.misptool.infrastructure.db.repositories import PostgresEventStateRepository


pytestmark = pytest.mark.skipif(
    not os.environ.get("MISP_DB_URL"),
    reason="MISP_DB_URL is not set",
)


def test_postgres_event_state_repository_round_trip():
    db = DbSession()
    Base.metadata.create_all(db.engine)

    with db.session() as session:
        repo = PostgresEventStateRepository(session)
        repo.update_event_state("42", {
            "event_id": "42",
            "info": "test event",
            "date": "2026-10-06",
            "timestamp": "1000",
            "publish_timestamp": "1001",
            "published": True,
            "threat_level_id": "1",
            "analysis": "0",
            "tag_names": [],
            "galaxy_tag_names": [],
            "attribute_count": 0,
            "object_count": 0,
            "score": 5,
            "fingerprint": "abc123",
        })
        repo.save()

    with db.session() as session:
        repo = PostgresEventStateRepository(session)
        state = repo.get_event_state("42")
        states = repo.list_event_states()

    assert state is not None
    assert state["event_id"] == "42"
    assert state["info"] == "test event"
    assert state["score"] == 5
    assert state["fingerprint"] == "abc123"
    assert any(item["event_id"] == "42" for item in states)
