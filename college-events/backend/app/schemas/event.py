from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import AnyHttpUrl, AwareDatetime, Field, field_validator, model_validator

from app.models.event import EventStatus
from app.schemas.common import Input, Output


class RegistrationAvailability(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FULL = "FULL"


class EventCreate(Input):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=1, max_length=50000)
    category: str = Field(min_length=1, max_length=80)
    poster_url: AnyHttpUrl | None = None
    venue: str = Field(min_length=1, max_length=200)
    start_time: AwareDatetime
    end_time: AwareDatetime
    registration_deadline: AwareDatetime
    capacity: int = Field(ge=1, le=1000000)
    price: int = Field(default=0, ge=0, le=1000000)
    eligibility: str | None = Field(default=None, max_length=10000)
    rules: str | None = Field(default=None, max_length=20000)

    @field_validator("start_time", "end_time", "registration_deadline")
    @classmethod
    def utc_dates(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def date_order(self) -> "EventCreate":
        if self.end_time <= self.start_time:
            raise ValueError("Event end must be after its start.")
        if self.registration_deadline > self.start_time:
            raise ValueError("Registration deadline must not be later than event start.")
        return self


class EventUpdate(Input):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=50000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    poster_url: AnyHttpUrl | None = None
    venue: str | None = Field(default=None, min_length=1, max_length=200)
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    registration_deadline: AwareDatetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=1000000)
    price: int | None = Field(default=None, ge=0, le=1000000)
    eligibility: str | None = Field(default=None, max_length=10000)
    rules: str | None = Field(default=None, max_length=20000)

    @field_validator("start_time", "end_time", "registration_deadline")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value else None

    @model_validator(mode="after")
    def required_values(self) -> "EventUpdate":
        nullable = {"poster_url", "eligibility", "rules"}
        for name in self.model_fields_set - nullable:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null.")
        return self


class OrganizerOut(Output):
    id: UUID
    full_name: str


class EventOut(Output):
    id: UUID
    title: str
    slug: str
    description: str
    category: str
    poster_url: str | None
    venue: str
    start_time: datetime
    end_time: datetime
    registration_deadline: datetime
    capacity: int
    price: int
    eligibility: str | None
    rules: str | None
    organizer_id: UUID
    organizer: OrganizerOut
    status: EventStatus
    registered_count: int
    available_seats: int
    registration_available: bool
    registration_status: RegistrationAvailability
    created_at: datetime
    updated_at: datetime


class PosterOut(Output):
    poster_url: str
