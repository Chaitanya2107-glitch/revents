from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import EventStatus, RegistrationStatus
from app.schemas.common import Output, Page


class StudentIdentity(Output):
    id: UUID
    full_name: str
    email: str
    department: str | None
    academic_year: int | None
    student_id: str | None


class ManagerRegistrationOut(BaseModel):
    id: UUID
    event_id: UUID
    student: StudentIdentity
    status: RegistrationStatus
    registered_at: datetime
    cancelled_at: datetime | None
    ticket_number: str | None
    checked_in_at: datetime | None


class RegistrationActivity(BaseModel):
    registration_id: UUID
    event_id: UUID
    event_title: str
    student_name: str
    status: RegistrationStatus
    registered_at: datetime


class ManagerDashboard(BaseModel):
    total_events: int
    upcoming_events: int
    published_events: int
    total_registrations: int
    confirmed_registrations: int
    total_checked_in: int
    recent_registration_activity: list[RegistrationActivity]


class CategoryCount(BaseModel):
    category: str
    count: int


class StatusCount(BaseModel):
    status: EventStatus
    count: int


class EventRegistrationCount(BaseModel):
    event_id: UUID
    event_title: str
    total_registrations: int
    confirmed_registrations: int


class EventAttendanceCount(BaseModel):
    event_id: UUID
    event_title: str
    attended: int
    total_check_ins: int
    total_confirmed: int
    attendance_rate: float


class RegistrationTrend(BaseModel):
    date: date
    registrations: int


class ManagerAnalytics(BaseModel):
    events_by_category: list[CategoryCount]
    events_by_status: list[StatusCount]
    registrations_per_event: Page[EventRegistrationCount]
    attendance_per_event: Page[EventAttendanceCount]
    registration_trends: list[RegistrationTrend]
    trend_days: int
    total_confirmed: int
    confirmed_attended: int
    overall_attendance_rate: float
