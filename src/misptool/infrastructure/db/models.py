from sqlalchemy import Boolean, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventState(Base):
    __tablename__ = "event_states"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    info: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    publish_timestamp: Mapped[str] = mapped_column(String, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    threat_level_id: Mapped[str] = mapped_column(String, nullable=False)
    analysis: Mapped[str] = mapped_column(String, nullable=False)
    attribute_count: Mapped[int] = mapped_column(Integer, nullable=False)
    object_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False)
    tag_names: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    galaxy_tag_names: Mapped[list[str]] = mapped_column(JSON, nullable=False)

class EventChange(Base):
    __tablename__ = "event_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("event_states.event_id"), nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String, nullable=False)
    old_fingerprint: Mapped[str | None] = mapped_column(String, nullable=True)
    new_fingerprint: Mapped[str] = mapped_column(String, nullable=False)
    old_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_score: Mapped[int] = mapped_column(Integer, nullable=False)
    change_summary: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    observed_at: Mapped[str] = mapped_column(String, nullable=False)