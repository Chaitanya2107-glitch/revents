from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import utcnow
from app.errors import fail
from app.models import (
    Event,
    EventStatus,
    Notification,
    NotificationType,
    Registration,
    RegistrationStatus,
    User,
)
from app.services.event_service import confirmed_count
from app.services.ticket_service import issue_ticket


def registration_query():
    return select(Registration).options(
        selectinload(Registration.event),
        selectinload(Registration.ticket),
        selectinload(Registration.attendance),
    )


def owned_registration(db: Session, registration_id: UUID, student: User) -> Registration:
    registration = db.scalar(registration_query().where(Registration.id == registration_id))
    if registration is None:
        fail(404, "REGISTRATION_NOT_FOUND", "Registration not found.")
    if registration.student_id != student.id:
        fail(403, "REGISTRATION_FORBIDDEN", "You cannot access this registration.")
    return registration


def registration_output(registration: Registration) -> dict:
    attendance = registration.attendance
    return {
        "id": registration.id,
        "student_id": registration.student_id,
        "event_id": registration.event_id,
        "status": registration.status,
        "registered_at": registration.registered_at,
        "cancelled_at": registration.cancelled_at,
        "event": registration.event,
        "ticket": registration.ticket,
        "checked_in": attendance is not None,
        "checked_in_at": attendance.checked_in_at if attendance else None,
    }


def register(db: Session, event_id: UUID, student: User) -> Registration:
    # Every seat-affecting operation locks the same event before reading booking counts.
    event = db.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if event is None:
        fail(404, "EVENT_NOT_FOUND", "Event not found.")
    if event.status == EventStatus.CANCELLED:
        fail(409, "EVENT_CANCELLED", "This event has been cancelled.")
    if event.status == EventStatus.COMPLETED:
        fail(409, "EVENT_COMPLETED", "This event has completed.")
    if event.status != EventStatus.PUBLISHED:
        fail(409, "EVENT_NOT_PUBLISHED", "This event is not open for registration.")
    now = utcnow()
    if now >= event.registration_deadline or now >= event.start_time:
        fail(409, "REGISTRATION_CLOSED", "The registration deadline has passed.")
    duplicate = db.scalar(select(Registration.id).where(
        Registration.event_id == event.id,
        Registration.student_id == student.id,
        Registration.status == RegistrationStatus.CONFIRMED,
    ))
    if duplicate:
        fail(409, "ALREADY_REGISTERED", "You are already registered for this event.")
    if confirmed_count(db, event.id) >= event.capacity:
        fail(409, "EVENT_FULL", "Registration is closed because the event is full.")
    registration = Registration(
        student_id=student.id, event_id=event.id, status=RegistrationStatus.CONFIRMED,
        registered_at=now,
    )
    db.add(registration)
    db.flush()
    issue_ticket(db, registration)
    db.add(Notification(
        user_id=student.id, title="Registration confirmed",
        message=f"Your booking for {event.title} is confirmed. Your entry pass is available.",
        type=NotificationType.BOOKING_CONFIRMED,
    ))
    db.flush()
    return db.scalar(registration_query().where(Registration.id == registration.id)
                     .execution_options(populate_existing=True))


def cancel(db: Session, registration_id: UUID, student: User) -> Registration:
    registration = owned_registration(db, registration_id, student)
    event = db.scalar(select(Event).where(Event.id == registration.event_id).with_for_update()
                      .execution_options(populate_existing=True))
    registration = db.scalar(registration_query().where(Registration.id == registration_id)
                             .with_for_update().execution_options(populate_existing=True))
    if registration.status == RegistrationStatus.CANCELLED:
        fail(409, "ALREADY_CANCELLED", "This booking is already cancelled.")
    if registration.attendance is not None:
        fail(409, "ALREADY_CHECKED_IN", "A checked-in booking cannot be cancelled.")
    now = utcnow()
    cutoff = event.start_time - timedelta(hours=get_settings().cancellation_cutoff_hours)
    if event.status != EventStatus.PUBLISHED or now >= cutoff:
        fail(409, "CANCELLATION_CLOSED", "The cancellation cutoff has passed.")
    registration.status = RegistrationStatus.CANCELLED
    registration.cancelled_at = now
    if registration.ticket:
        registration.ticket.revoked_at = now
    db.add(Notification(
        user_id=student.id, title="Booking cancelled",
        message=f"Your booking for {event.title} was cancelled.",
        type=NotificationType.BOOKING_CANCELLED,
    ))
    db.flush()
    return registration

