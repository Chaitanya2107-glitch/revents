from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.registration import RegistrationStatus
from app.schemas.common import Input, Output


class TicketCheckin(Input):
    event_id: UUID
    qr_token: str = Field(min_length=1, max_length=256)


class TicketOut(Output):
    id: UUID
    registration_id: UUID
    event_id: UUID
    ticket_number: str
    app_name: str
    event_title: str
    start_time: datetime
    end_time: datetime
    venue: str
    student_name: str
    status: RegistrationStatus
    issued_at: datetime
    revoked_at: datetime | None
    qr_token: str | None = None
    qr_image_data_url: str | None = None
    qr_expires_at: datetime | None = None
