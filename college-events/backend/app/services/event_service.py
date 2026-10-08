import re
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, insert, literal, select, update
from sqlalchemy.orm import Session

from app.database import utcnow
from app.errors import fail
from app.models import (
    Event, EventStatus, Notification, NotificationType, Registration, RegistrationStatus,
    Ticket, User,
)
from app.schemas.common import page_result
from app.schemas.event import EventCreate, EventUpdate, RegistrationAvailability


def get_event(db: Session, event_id: UUID) -> Event:
    event = db.get(Event, event_id)
    if not event:
        fail(404, "EVENT_NOT_FOUND", "Event not found.")
    return event


def managed_event(db: Session, event_id: UUID, manager: User, lock: bool = False) -> Event:
    query = select(Event).where(Event.id == event_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    event = db.scalar(query)
    if not event:
        fail(404, "EVENT_NOT_FOUND", "Event not found.")
    if event.organizer_id != manager.id:
        fail(403, "EVENT_FORBIDDEN", "You do not manage this event.")
    return event


def confirmed_count(db: Session, event_id: UUID) -> int:
    return db.scalar(select(func.count()).select_from(Registration).where(
        Registration.event_id == event_id, Registration.status == RegistrationStatus.CONFIRMED
    )) or 0


def event_dict(event: Event, organizer: User, count: int) -> dict:
    seats = max(0, event.capacity - count)
    availability = RegistrationAvailability.OPEN
    if event.status != EventStatus.PUBLISHED or event.registration_deadline <= utcnow():
        availability = RegistrationAvailability.CLOSED
    elif not seats:
        availability = RegistrationAvailability.FULL
    return {
        "id": event.id, "title": event.title, "slug": event.slug,
        "description": event.description, "category": event.category,
        "poster_url": event.poster_url, "venue": event.venue,
        "start_time": event.start_time, "end_time": event.end_time,
        "registration_deadline": event.registration_deadline, "capacity": event.capacity,
        "eligibility": event.eligibility, "rules": event.rules,
        "organizer_id": event.organizer_id,
        "organizer": {"id": organizer.id, "full_name": organizer.full_name},
        "status": event.status, "registered_count": count, "available_seats": seats,
        "registration_available": availability == RegistrationAvailability.OPEN,
        "registration_status": availability, "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def event_output(db: Session, event: Event) -> dict:
    return event_dict(event, db.get(User, event.organizer_id), confirmed_count(db, event.id))


def notify_registered_students(
    db: Session, event: Event, title: str, message: str, kind: NotificationType
) -> None:
    # Build notification rows in PostgreSQL rather than loading every booking into memory.
    recipients = select(
        func.gen_random_uuid(), Registration.student_id,
        literal(title), literal(message), literal(kind.value), literal(False), literal(utcnow()),
    ).where(Registration.event_id == event.id,
            Registration.status == RegistrationStatus.CONFIRMED)
    db.execute(insert(Notification).from_select(
        ["id", "user_id", "title", "message", "type", "is_read", "created_at"], recipients
    ))


def list_events(
    db: Session, page: int, page_size: int, search: str | None = None,
    category: str | None = None, event_date: date | None = None,
    date_from: datetime | None = None, date_to: datetime | None = None,
    registration_status: RegistrationAvailability | None = None,
    status: EventStatus | None = None, upcoming_only: bool = False,
) -> dict:
    counts = select(Registration.event_id, func.count().label("registered_count")).where(
        Registration.status == RegistrationStatus.CONFIRMED
    ).group_by(Registration.event_id).subquery()
    count = func.coalesce(counts.c.registered_count, 0)
    filters = [Event.status == (status or EventStatus.PUBLISHED)]
    if search:
        search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        filters.append(Event.title.ilike(f"%{search}%", escape="\\"))
    if category:
        filters.append(func.lower(Event.category) == category.lower())
    if status is not None:
        filters.append(Event.status == status)
    if event_date:
        day_start = datetime.combine(event_date, time.min, tzinfo=UTC)
        filters.extend([Event.start_time >= day_start, Event.start_time < day_start + timedelta(days=1)])
    if date_from:
        filters.append(Event.start_time >= date_from)
    if date_to:
        filters.append(Event.start_time <= date_to)
    now = utcnow()
    if upcoming_only:
        filters.append(Event.start_time > now)
    open_conditions = [Event.status == EventStatus.PUBLISHED, Event.registration_deadline > now]
    if registration_status == RegistrationAvailability.OPEN:
        filters.extend([*open_conditions, count < Event.capacity])
    elif registration_status == RegistrationAvailability.FULL:
        filters.extend([*open_conditions, count >= Event.capacity])
    elif registration_status == RegistrationAvailability.CLOSED:
        filters.append((Event.status != EventStatus.PUBLISHED) | (Event.registration_deadline <= now))
    query = select(Event, User, count).join(User, User.id == Event.organizer_id).outerjoin(
        counts, counts.c.event_id == Event.id
    ).where(*filters)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(Event.start_time, Event.id).offset(
        (page - 1) * page_size
    ).limit(page_size)).all()
    return page_result([event_dict(event, organizer, total_count)
                        for event, organizer, total_count in rows], total, page, page_size)


def create_event(db: Session, manager: User, data: EventCreate) -> Event:
    if data.start_time <= utcnow():
        fail(422, "INVALID_START_TIME", "New events must start in the future.")
    values = data.model_dump()
    if values["poster_url"] is not None:
        values["poster_url"] = str(values["poster_url"])
    slug = re.sub(r"[^a-z0-9]+", "-", data.title.lower()).strip("-") or "event"
    event = Event(**values, slug=f"{slug[:220]}-{uuid4().hex[:12]}", organizer_id=manager.id,
                  status=EventStatus.DRAFT)
    db.add(event)
    db.flush()
    return event


def update_event(db: Session, event_id: UUID, manager: User, data: EventUpdate) -> Event:
    event = managed_event(db, event_id, manager, lock=True)
    if event.status in {EventStatus.CANCELLED, EventStatus.COMPLETED} or event.start_time <= utcnow():
        fail(409, "EVENT_NOT_EDITABLE", "Cancelled, completed, or started events cannot be edited.")
    changes = data.model_dump(exclude_unset=True)
    if "poster_url" in changes and changes["poster_url"] is not None:
        changes["poster_url"] = str(changes["poster_url"])
    changes = {name: value for name, value in changes.items() if getattr(event, name) != value}
    if not changes:
        return event
    has_bookings = db.scalar(select(Registration.id).where(
        Registration.event_id == event.id
    ).limit(1)) is not None
    if has_bookings and {"start_time", "end_time", "registration_deadline"} & changes.keys():
        fail(409, "EVENT_SCHEDULE_LOCKED", "Schedule changes are disabled after the first booking.")
    start = changes.get("start_time", event.start_time)
    end = changes.get("end_time", event.end_time)
    deadline = changes.get("registration_deadline", event.registration_deadline)
    if start <= utcnow() or end <= start or deadline > start:
        fail(422, "INVALID_EVENT_DATES", "Use a future start, a later end, and deadline before start.")
    if changes.get("capacity", event.capacity) < confirmed_count(db, event.id):
        fail(409, "CAPACITY_TOO_SMALL", "Capacity cannot be smaller than confirmed registrations.")
    for name, value in changes.items():
        setattr(event, name, value)
    if has_bookings:
        notify_registered_students(db, event, "Event updated", f"Details for {event.title} changed. "
                                   "Please review the event before attending.", NotificationType.EVENT_UPDATED)
    db.flush()
    return event


def publish_event(db: Session, event_id: UUID, manager: User) -> Event:
    event = managed_event(db, event_id, manager, lock=True)
    if event.status != EventStatus.DRAFT:
        fail(409, "EVENT_NOT_DRAFT", "Only draft events can be published.")
    now = utcnow()
    if event.start_time <= now or event.registration_deadline <= now:
        fail(422, "INVALID_EVENT_DATES", "Publishing requires future event and registration dates.")
    event.status = EventStatus.PUBLISHED
    db.flush()
    return event


def cancel_event(db: Session, event_id: UUID, manager: User) -> Event:
    event = managed_event(db, event_id, manager, lock=True)
    if event.status == EventStatus.CANCELLED:
        return event
    if event.status == EventStatus.DRAFT:
        fail(409, "EVENT_NOT_PUBLISHED", "Delete an unpublished draft instead of cancelling it.")
    if event.status == EventStatus.COMPLETED or event.end_time <= utcnow():
        fail(409, "EVENT_COMPLETED", "Completed events cannot be cancelled.")
    now = utcnow()
    notify_registered_students(db, event, "Event cancelled", f"{event.title} has been cancelled.",
                               NotificationType.EVENT_CANCELLED)
    registration_ids = select(Registration.id).where(Registration.event_id == event.id)
    db.execute(update(Ticket).where(Ticket.registration_id.in_(registration_ids),
                                   Ticket.revoked_at.is_(None)).values(revoked_at=now))
    db.execute(update(Registration).where(
        Registration.event_id == event.id, Registration.status == RegistrationStatus.CONFIRMED
    ).values(status=RegistrationStatus.CANCELLED, cancelled_at=now))
    event.status = EventStatus.CANCELLED
    db.flush()
    return event


def delete_event(db: Session, event_id: UUID, manager: User) -> None:
    event = managed_event(db, event_id, manager, lock=True)
    if event.status != EventStatus.DRAFT:
        fail(409, "EVENT_DELETE_FORBIDDEN", "Only drafts without booking history may be deleted.")
    if db.scalar(select(Registration.id).where(Registration.event_id == event.id).limit(1)):
        fail(409, "EVENT_HAS_BOOKINGS", "Cancel events with booking history instead of deleting them.")
    db.delete(event)
    db.flush()


def complete_event(db: Session, event_id: UUID, manager: User) -> Event:
    event = managed_event(db, event_id, manager, lock=True)
    if event.status != EventStatus.PUBLISHED or event.end_time > utcnow():
        fail(409, "EVENT_NOT_FINISHED", "Only published events that have ended can be completed.")
    event.status = EventStatus.COMPLETED
    db.flush()
    return event
