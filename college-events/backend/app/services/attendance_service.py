import hmac
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import utcnow
from app.errors import fail
from app.models import Attendance, EventStatus, Registration, RegistrationStatus, Ticket, User
from app.services.event_service import managed_event
from app.services.ticket_service import parse_presentation_token


def verify_checkin(db: Session, event_id: UUID, qr_token: str, manager: User) -> Attendance:
    event = managed_event(db, event_id, manager, lock=True)
    ticket_id, credential_hash = parse_presentation_token(qr_token)
    registration = db.scalar(
        select(Registration).join(Ticket).where(Ticket.id == ticket_id).options(
            selectinload(Registration.student),
            selectinload(Registration.ticket),
            selectinload(Registration.attendance),
        ).execution_options(populate_existing=True)
    )
    ticket = registration.ticket if registration is not None else None
    if ticket is None or not hmac.compare_digest(ticket.qr_token_hash, credential_hash):
        fail(400, "INVALID_QR", "The QR ticket is invalid.")
    if registration.event_id != event_id:
        fail(400, "WRONG_EVENT", "This ticket belongs to a different event.")
    if ticket.revoked_at is not None:
        fail(409, "REVOKED_TICKET", "This ticket has been revoked.")
    if registration.status != RegistrationStatus.CONFIRMED:
        fail(409, "REGISTRATION_CANCELLED", "This registration is not confirmed.")
    if registration.attendance is not None:
        fail(409, "ALREADY_CHECKED_IN", "This ticket has already been checked in.")
    settings = get_settings()
    now = utcnow()
    if (event.status != EventStatus.PUBLISHED
            or now < event.start_time - timedelta(minutes=settings.checkin_before_minutes)
            or now > event.end_time + timedelta(minutes=settings.checkin_after_minutes)):
        fail(409, "CHECKIN_CLOSED", "Check-in is outside the event's allowed entry window.")
    attendance = Attendance(registration_id=registration.id, checked_in_by=manager.id,
                            checked_in_at=now, registration=registration)
    db.add(attendance)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            fail(409, "ALREADY_CHECKED_IN", "This ticket has already been checked in.")
        raise
    return attendance
