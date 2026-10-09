from fastapi import APIRouter, Depends, HTTPException

from src.misptool.api.dependencies import get_event_state_repo
from src.misptool.application.ports import EventStateRepository
from src.misptool.api.schemas import EventStateResponse
from src.misptool.application.filters import EventStateFilters


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/events",
response_model=list[EventStateResponse])
def list_events(
    limit: int = 50,
    min_score: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    published: bool | None = None,
    repo: EventStateRepository = Depends(get_event_state_repo),
) -> list[dict]:
    filters = EventStateFilters(
        limit=limit,
        min_score=min_score,
        from_date=from_date,
        to_date=to_date,
        published=published,
    )
    return repo.list_event_states(filters)


@router.get("/events/{event_id}",
response_model=EventStateResponse)
def get_event_by_id(
    event_id: str,
    repo: EventStateRepository = Depends(get_event_state_repo),
) -> dict:
    result = repo.get_event_state(event_id)

    if result is None:
        raise HTTPException(404, detail=("wrong event id: " + event_id))
    
    return result