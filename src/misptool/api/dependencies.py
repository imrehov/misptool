from collections.abc import Iterator

from src.misptool.application.ports import EventStateRepository
from src.misptool.infrastructure.db.repositories import PostgresEventStateRepository
from src.misptool.infrastructure.db.session import DbSession


def get_event_state_repo() -> Iterator[EventStateRepository]:
    db = DbSession()

    with db.session() as session:
        yield PostgresEventStateRepository(session)
