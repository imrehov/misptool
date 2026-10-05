from sqlalchemy import Boolean, Integer, String, JSON
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