from fastapi import APIRouter, Depends, HTTPException

from src.misptool.api.dependencies import get_event_state_repo
from src.misptool.application.ports import EventStateRepository


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/events")
def list_events(
    repo: EventStateRepository = Depends(get_event_state_repo),
    limit: int = 50,
) -> list[dict]:
    return repo.list_event_states(limit)


@router.get("/events/{event_id}")
def get_event_by_id(
    event_id: str,
    repo: EventStateRepository = Depends(get_event_state_repo),
) -> dict | None:
    result = repo.get_event_state(event_id)

    if result is None:
        raise HTTPException(404, detail=("wrong event id: " + event_id))
    
    return result