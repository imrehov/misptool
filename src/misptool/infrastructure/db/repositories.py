from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.misptool.infrastructure.db.models import EventState


class PostgresEventStateRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_event_state(self, event_id: str) -> dict[str, Any] | None:
        row = self.session.get(EventState, str(event_id))

        if row is None:
            return None

        return self._row_to_dict(row)

    def _row_to_dict(self, row: EventState) -> dict[str, Any]:
        return {
            "event_id": row.event_id,
            "info": row.info,
            "date": row.date,
            "timestamp": row.timestamp,
            "publish_timestamp": row.publish_timestamp,
            "published": row.published,
            "threat_level_id": row.threat_level_id,
            "analysis": row.analysis,
            "tag_names": row.tag_names,
            "galaxy_tag_names": row.galaxy_tag_names,
            "attribute_count": row.attribute_count,
            "object_count": row.object_count,
            "score": row.score,
            "fingerprint": row.fingerprint,
        }

    def update_event_state(self, event_id: str, state: dict[str, Any]) -> None:
        event_state = EventState(
            event_id=str(event_id),
            info=state["info"],
            date=state["date"],
            timestamp=state["timestamp"],
            publish_timestamp=state["publish_timestamp"],
            published=state["published"],
            threat_level_id=state["threat_level_id"],
            analysis=state["analysis"],
            tag_names=state["tag_names"],
            galaxy_tag_names=state["galaxy_tag_names"],
            attribute_count=state["attribute_count"],
            object_count=state["object_count"],
            score=state["score"],
            fingerprint=state["fingerprint"],
        )
        
        self.session.merge(event_state)
   

    def save(self) -> None:
        self.session.commit()

    def list_event_states(self, limit: int = 50) -> list[dict[str, Any]]:
        statement = (
            select(EventState)
            .order_by(desc(EventState.event_id))
            .limit(limit)
        )

        rows = self.session.scalars(statement).all()

        return [self._row_to_dict(row) for row in rows]
