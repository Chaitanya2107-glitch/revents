from datetime import timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Subquery

from app.database import utcnow
from app.dependencies import Db, Manager
from app.models import Attendance, Event, EventStatus, Registration, RegistrationStatus, User
from app.schemas.attendance import AttendanceOut, AttendanceSummary
from app.schemas.common import Page, page_result
from app.schemas.event import EventOut
from app.schemas.manager import ManagerAnalytics, ManagerDashboard, ManagerRegistrationOut
from app.services.event_service import event_dict, managed_event

router = APIRouter(prefix="/api/manager", tags=["manager"])


def registration_counts(manager_id: UUID) -> Subquery:
    return (select(
        Registration.event_id,
        func.count(Registration.id).label("total"),
        func.count(Registration.id).filter(
            Registration.status == RegistrationStatus.CONFIRMED
        ).label("confirmed"),
        func.count(Attendance.id).label("check_ins"),
        func.count(Attendance.id).filter(
            Registration.status == RegistrationStatus.CONFIRMED
        ).label("attended"),
    ).select_from(Registration).join(Event, Registration.event_id == Event.id)
        .outerjoin(Attendance, Attendance.registration_id == Registration.id)
        .where(Event.organizer_id == manager_id)
        .group_by(Registration.event_id).subquery())


@router.get("/dashboard", response_model=ManagerDashboard)
def dashboard(manager: Manager, db: Db) -> dict:
    now = utcnow()
    events = db.execute(select(
        func.count(Event.id).label("total_events"),
        func.count(Event.id).filter(
            Event.start_time > now,
            Event.status.in_([EventStatus.DRAFT, EventStatus.PUBLISHED]),
        ).label("upcoming_events"),
        func.count(Event.id).filter(Event.status == EventStatus.PUBLISHED)
            .label("published_events"),
    ).where(Event.organizer_id == manager.id)).one()
    counts = registration_counts(manager.id)
    registrations = db.execute(select(
        func.coalesce(func.sum(counts.c.total), 0).label("total_registrations"),
        func.coalesce(func.sum(counts.c.confirmed), 0).label("confirmed_registrations"),
        func.coalesce(func.sum(counts.c.check_ins), 0).label("total_checked_in"),
    )).one()
    recent = db.execute(select(
        Registration.id.label("registration_id"), Registration.event_id,
        Event.title.label("event_title"), User.full_name.label("student_name"),
        Registration.status, Registration.registered_at,
    ).select_from(Registration).join(Event, Registration.event_id == Event.id)
        .join(User, Registration.student_id == User.id)
        .where(Event.organizer_id == manager.id)
        .order_by(Registration.registered_at.desc(), Registration.id).limit(10)).all()
    return {**events._mapping, **registrations._mapping,
            "recent_registration_activity": [dict(row._mapping) for row in recent]}


@router.get("/events", response_model=Page[EventOut])
def manager_events(
    manager: Manager,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: EventStatus | None = None,
) -> dict:
    filters = [Event.organizer_id == manager.id]
    if status is not None:
        filters.append(Event.status == status)
    total = db.scalar(select(func.count()).select_from(Event).where(*filters)) or 0
    counts = registration_counts(manager.id)
    rows = db.execute(select(Event, func.coalesce(counts.c.confirmed, 0))
        .outerjoin(counts, Event.id == counts.c.event_id).where(*filters)
        .order_by(Event.start_time, Event.id).offset((page - 1) * page_size).limit(page_size))
    return page_result([event_dict(event, manager, count) for event, count in rows],
                       total, page, page_size)


@router.get("/events/{event_id}/registrations", response_model=Page[ManagerRegistrationOut])
def event_registrations(
    event_id: UUID,
    manager: Manager,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Literal["confirmed", "cancelled", "checked_in", "not_checked_in"] | None = None,
) -> dict:
    managed_event(db, event_id, manager)
    filters = [Registration.event_id == event_id]
    if status in ("confirmed", "cancelled"):
        filters.append(Registration.status == RegistrationStatus(status.upper()))
    elif status == "checked_in":
        filters.append(Registration.attendance.has())
    elif status == "not_checked_in":
        filters.extend([Registration.status == RegistrationStatus.CONFIRMED,
                        ~Registration.attendance.has()])
    total = db.scalar(select(func.count()).select_from(Registration).where(*filters)) or 0
    registrations = db.scalars(select(Registration).where(*filters).options(
        joinedload(Registration.student), joinedload(Registration.ticket),
        joinedload(Registration.attendance),
    ).order_by(Registration.registered_at.desc(), Registration.id)
        .offset((page - 1) * page_size).limit(page_size))
    items = [{"id": registration.id, "event_id": registration.event_id,
              "student": registration.student, "status": registration.status,
              "registered_at": registration.registered_at,
              "cancelled_at": registration.cancelled_at,
              "ticket_number": registration.ticket.ticket_number if registration.ticket else None,
              "checked_in_at": registration.attendance.checked_in_at
                  if registration.attendance else None} for registration in registrations]
    return page_result(items, total, page, page_size)


@router.get("/events/{event_id}/attendance", response_model=Page[AttendanceOut])
def event_attendance(
    event_id: UUID,
    manager: Manager,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    managed_event(db, event_id, manager)
    total = db.scalar(select(func.count()).select_from(Attendance)
        .join(Registration, Attendance.registration_id == Registration.id)
        .where(Registration.event_id == event_id)) or 0
    records = db.scalars(select(Attendance)
        .join(Registration, Attendance.registration_id == Registration.id)
        .where(Registration.event_id == event_id).options(
            joinedload(Attendance.registration).joinedload(Registration.student),
            joinedload(Attendance.registration).joinedload(Registration.ticket),
        ).order_by(Attendance.checked_in_at.desc(), Attendance.id)
        .offset((page - 1) * page_size).limit(page_size))
    items = [{"id": attendance.id, "registration_id": attendance.registration_id,
              "checked_in_at": attendance.checked_in_at, "checked_in_by": attendance.checked_in_by,
              "student_id": attendance.registration.student_id,
              "student_name": attendance.registration.student.full_name,
              "ticket_number": attendance.registration.ticket.ticket_number}
             for attendance in records]
    return page_result(items, total, page, page_size)


@router.get("/events/{event_id}/attendance/summary", response_model=AttendanceSummary)
def attendance_summary(event_id: UUID, manager: Manager, db: Db) -> dict:
    managed_event(db, event_id, manager)
    counts = registration_counts(manager.id)
    row = db.execute(select(counts).where(counts.c.event_id == event_id)).first()
    confirmed, attended, total_check_ins = (row.confirmed, row.attended, row.check_ins) if row else (0, 0, 0)
    return {"event_id": event_id, "attended": attended,
            "not_yet_checked_in": confirmed - attended, "total_confirmed": confirmed,
            "total_check_ins": total_check_ins}


@router.get("/analytics", response_model=ManagerAnalytics)
def analytics(
    manager: Manager,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    trend_days: Annotated[int, Query(ge=1, le=366)] = 30,
) -> dict:
    """Rates are percentages of confirmed registrations; historical check-ins remain separate."""
    categories = db.execute(select(Event.category, func.count(Event.id).label("count"))
        .where(Event.organizer_id == manager.id).group_by(Event.category)
        .order_by(Event.category)).all()
    statuses = db.execute(select(Event.status, func.count(Event.id).label("count"))
        .where(Event.organizer_id == manager.id).group_by(Event.status)
        .order_by(Event.status)).all()
    total = db.scalar(select(func.count()).select_from(Event)
        .where(Event.organizer_id == manager.id)) or 0
    counts = registration_counts(manager.id)
    event_rows = db.execute(select(
        Event.id.label("event_id"), Event.title.label("event_title"),
        func.coalesce(counts.c.total, 0).label("total_registrations"),
        func.coalesce(counts.c.confirmed, 0).label("confirmed"),
        func.coalesce(counts.c.check_ins, 0).label("check_ins"),
        func.coalesce(counts.c.attended, 0).label("attended"),
    ).outerjoin(counts, counts.c.event_id == Event.id)
        .where(Event.organizer_id == manager.id).order_by(Event.start_time, Event.id)
        .offset((page - 1) * page_size).limit(page_size)).all()
    totals = db.execute(select(func.coalesce(func.sum(counts.c.confirmed), 0),
                              func.coalesce(func.sum(counts.c.attended), 0))).one()
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=trend_days - 1)
    trends = db.execute(select(func.date(Registration.registered_at).label("date"),
        func.count(Registration.id).label("registrations"))
        .select_from(Registration).join(Event, Registration.event_id == Event.id)
        .where(Event.organizer_id == manager.id, Registration.registered_at >= start,
               Registration.registered_at < today + timedelta(days=1))
        .group_by(func.date(Registration.registered_at))
        .order_by(func.date(Registration.registered_at))).all()
    registrations = [{"event_id": row.event_id, "event_title": row.event_title,
                      "total_registrations": row.total_registrations,
                      "confirmed_registrations": row.confirmed} for row in event_rows]
    attendance = [{"event_id": row.event_id, "event_title": row.event_title,
                   "attended": row.attended, "total_check_ins": row.check_ins,
                   "total_confirmed": row.confirmed,
                   "attendance_rate": round(row.attended / row.confirmed * 100, 2)
                       if row.confirmed else 0.0} for row in event_rows]
    return {"events_by_category": [dict(row._mapping) for row in categories],
            "events_by_status": [dict(row._mapping) for row in statuses],
            "registrations_per_event": page_result(registrations, total, page, page_size),
            "attendance_per_event": page_result(attendance, total, page, page_size),
            "registration_trends": [dict(row._mapping) for row in trends],
            "trend_days": trend_days, "total_confirmed": totals[0], "confirmed_attended": totals[1],
            "overall_attendance_rate": round(totals[1] / totals[0] * 100, 2) if totals[0] else 0.0}
