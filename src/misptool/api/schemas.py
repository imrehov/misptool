from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: SecretStr = Field(min_length=1, max_length=128)

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
    misp_event_url: str

class EventChangeResponse(BaseModel):
    id: int | None = None
    event_id: str
    change_type: str
    old_fingerprint: str | None
    new_fingerprint: str
    old_score: int | None
    new_score: int
    change_summary: list[str]
    observed_at: str
