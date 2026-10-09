from fastapi import APIRouter

from src.misptool.infrastructure.db.repositories import PostgresEventStateRepository
from src.misptool.infrastructure.db.session import DbSession


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/events")
def list_events(limit: int = 50) -> list[dict]:
    db = DbSession()

    with db.session() as session:
        repo = PostgresEventStateRepository(session)
        return repo.list_event_states(limit=limit)