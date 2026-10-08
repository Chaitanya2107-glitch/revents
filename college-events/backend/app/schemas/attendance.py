from datetime import datetime
from uuid import UUID

from app.schemas.common import Output


class AttendanceOut(Output):
    id: UUID
    registration_id: UUID
    checked_in_at: datetime
    checked_in_by: UUID
    student_id: UUID
    student_name: str
    ticket_number: str


class AttendanceSummary(Output):
    event_id: UUID
    attended: int
    not_yet_checked_in: int
    total_confirmed: int
    total_check_ins: int
