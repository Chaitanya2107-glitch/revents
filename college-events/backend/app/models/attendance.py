from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, IdentityMixin, utcnow


class Attendance(IdentityMixin, Base):
    __tablename__ = "attendance"
    registration_id: Mapped[UUID] = mapped_column(
        ForeignKey("registrations.id", ondelete="RESTRICT"), unique=True
    )
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    checked_in_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    registration: Mapped["Registration"] = relationship(back_populates="attendance", lazy="raise")
    manager: Mapped["User"] = relationship(lazy="raise")
