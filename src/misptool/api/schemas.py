from pydantic import BaseModel

class EventStateResponse(BaseModel):
    event_id: str
    info: str
    date: str
    timestamp: str
    publish_timestamp: str
    published: bool
    threat_level_id: str
    analysis: str
    tag_names: list[str]
    galaxy_tag_names: list[str]
    attribute_count: int
    object_count: int
    score: int
    fingerprint: str