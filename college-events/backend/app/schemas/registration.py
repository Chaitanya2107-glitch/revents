from datetime import datetime
from uuid import UUID

from app.models import EventStatus, RegistrationStatus
from app.schemas.common import Output


class BookingEvent(Output):
    id: UUID
    title: str
    venue: str
    start_time: datetime
    end_time: datetime
    status: EventStatus


class BookingTicket(Output):
    id: UUID
    ticket_number: str
    issued_at: datetime
    revoked_at: datetime | None


class RegistrationOut(Output):
    id: UUID
    student_id: UUID
    event_id: UUID
    status: RegistrationStatus
    registered_at: datetime
    cancelled_at: datetime | None
    event: BookingEvent
    ticket: BookingTicket | None
    checked_in: bool
    checked_in_at: datetime | None

