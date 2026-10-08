from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, IdentityMixin, utcnow


class Ticket(IdentityMixin, Base):
    __tablename__ = "tickets"
    registration_id: Mapped[UUID] = mapped_column(
        ForeignKey("registrations.id", ondelete="RESTRICT"), unique=True
    )
    ticket_number: Mapped[str] = mapped_column(String(40), unique=True)
    qr_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registration: Mapped["Registration"] = relationship(back_populates="ticket", lazy="raise")
