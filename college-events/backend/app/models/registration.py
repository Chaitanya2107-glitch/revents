from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, IdentityMixin, utcnow


class RegistrationStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Registration(IdentityMixin, Base):
    __tablename__ = "registrations"
    __table_args__ = (
        Index("uq_registrations_confirmed_student_event", "student_id", "event_id", unique=True,
              postgresql_where=text("status = 'CONFIRMED'")),
        Index("ix_registrations_event_status", "event_id", "status"),
        Index("ix_registrations_student_registered_at", "student_id", "registered_at"),
        CheckConstraint("(status = 'CONFIRMED' AND cancelled_at IS NULL) OR "
                        "(status = 'CANCELLED' AND cancelled_at IS NOT NULL)", name="cancellation_state"),
    )
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"))
    status: Mapped[RegistrationStatus] = mapped_column(Enum(RegistrationStatus,
        name="registration_status", native_enum=False, create_constraint=True),
        default=RegistrationStatus.CONFIRMED, server_default="CONFIRMED")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    student: Mapped["User"] = relationship(lazy="raise")
    event: Mapped["Event"] = relationship(lazy="raise")
    ticket: Mapped["Ticket | None"] = relationship(back_populates="registration", lazy="raise")
    attendance: Mapped["Attendance | None"] = relationship(back_populates="registration", lazy="raise")
