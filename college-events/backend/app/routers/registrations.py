from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.database import utcnow
from app.dependencies import Db, Student
from app.models import Event, EventStatus, Registration, RegistrationStatus
from app.schemas.common import Page, page_result
from app.schemas.registration import RegistrationOut
from app.services import registration_service as service

router = APIRouter(prefix="/api", tags=["registrations"])


@router.post("/events/{event_id}/register", response_model=RegistrationOut, status_code=201)
def register(event_id: UUID, user: Student, db: Db):
    return service.registration_output(service.register(db, event_id, user))


@router.get("/registrations/me", response_model=Page[RegistrationOut])
def bookings(
    user: Student,
    db: Db,
    period: Literal["upcoming", "past", "cancelled"] | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    conditions = [Registration.student_id == user.id]
    if period == "cancelled":
        conditions.append(Registration.status == RegistrationStatus.CANCELLED)
    elif period == "upcoming":
        conditions.extend([
            Registration.status == RegistrationStatus.CONFIRMED,
            Event.end_time > utcnow(), Event.status == EventStatus.PUBLISHED,
        ])
    elif period == "past":
        conditions.extend([
            Registration.status == RegistrationStatus.CONFIRMED,
            (Event.end_time <= utcnow()) | (Event.status == EventStatus.COMPLETED),
        ])
    total = db.scalar(select(func.count(Registration.id)).join(Event).where(*conditions)) or 0
    registrations = db.scalars(
        service.registration_query().join(Event).where(*conditions)
        .order_by(Registration.registered_at.desc(), Registration.id)
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return page_result([service.registration_output(r) for r in registrations], total, page, page_size)


@router.get("/registrations/{registration_id}", response_model=RegistrationOut)
def registration(registration_id: UUID, user: Student, db: Db):
    return service.registration_output(service.owned_registration(db, registration_id, user))


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationOut)
def cancel(registration_id: UUID, user: Student, db: Db):
    return service.registration_output(service.cancel(db, registration_id, user))
