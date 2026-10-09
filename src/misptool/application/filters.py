from dataclasses import dataclass


@dataclass
class EventStateFilters:
    limit: int = 50
    min_score: int | None = None
    from_date: str | None = None
    to_date: str | None = None
    published: bool | None = None