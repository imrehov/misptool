import json
import os
import uuid

import pytest

from src.misptool.application.cli_commands import CliCommands
from src.misptool.infrastructure.db.models import EventState
from src.misptool.infrastructure.db.session import DbSession


pytestmark = pytest.mark.skipif(
    not os.environ.get("MISP_DB_URL"),
    reason="MISP_DB_URL is not set",
)


def test_migrate_state_copies_json_snapshot_to_postgres(tmp_path):
    event_id = f"pytest-{uuid.uuid4()}"
    snapshot = {
        "event_id": event_id,
        "info": "pytest migration event",
        "date": "2026-10-07",
        "timestamp": "1791331200",
        "publish_timestamp": "1791331300",
        "published": True,
        "threat_level_id": "2",
        "analysis": "1",
        "tag_names": ["tlp:white", "pytest"],
        "galaxy_tag_names": ["threat-actor:test"],
        "attribute_count": 12,
        "object_count": 3,
        "score": 7,
        "fingerprint": "pytest-fingerprint",
    }

    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"events": {event_id: snapshot}}),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'storage:\n  database_url_env: "MISP_DB_URL"\n',
        encoding="utf-8",
    )

    try:
        CliCommands(str(config_path)).migrate_state(str(state_path))

        with DbSession().session() as session:
            row = session.get(EventState, event_id)

            assert row is not None
            assert row.info == "pytest migration event"
            assert row.score == 7
            assert row.tag_names == ["tlp:white", "pytest"]
            assert row.galaxy_tag_names == ["threat-actor:test"]

    finally:
        with DbSession().session() as session:
            row = session.get(EventState, event_id)

            if row is not None:
                session.delete(row)
                session.commit()
