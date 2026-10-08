from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, IdentityMixin, TimestampMixin


class EventStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Event(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="positive_capacity"),
        CheckConstraint("end_time > start_time", name="valid_dates"),
        CheckConstraint("registration_deadline <= start_time", name="valid_deadline"),
        Index("ix_events_status_start_time", "status", "start_time"),
        Index("ix_events_category_start_time", "category", "start_time"),
    )
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(240), unique=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80))
    poster_url: Mapped[str | None] = mapped_column(String(2048))
    venue: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int]
    price: Mapped[int] = mapped_column(default=0, server_default="0")
    eligibility: Mapped[str | None] = mapped_column(Text)
    rules: Mapped[str | None] = mapped_column(Text)
    organizer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name="event_status",
                                                  native_enum=False, create_constraint=True),
                                              default=EventStatus.DRAFT, server_default="DRAFT")
    organizer: Mapped["User"] = relationship(lazy="raise")
