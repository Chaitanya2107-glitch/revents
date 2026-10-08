from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, File, Query, Response, UploadFile
from pydantic import AwareDatetime

from app.dependencies import Db, Manager
from app.errors import fail
from app.models.event import EventStatus
from app.schemas.common import Page
from app.schemas.event import EventCreate, EventOut, EventUpdate, PosterOut, RegistrationAvailability
from app.services import event_service, upload_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=Page[EventOut])
def browse_events(
    db: Db, page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    event_date: Annotated[date | None, Query(alias="date")] = None,
    date_from: Annotated[AwareDatetime | None, Query()] = None,
    date_to: Annotated[AwareDatetime | None, Query()] = None,
    registration_status: RegistrationAvailability | None = None,
    status: Literal["PUBLISHED", "CANCELLED", "COMPLETED"] | None = None,
    upcoming_only: bool = False,
):
    if date_from and date_to and date_from > date_to:
        fail(422, "INVALID_DATE_RANGE", "date_from must not be later than date_to.")
    return event_service.list_events(db, page, page_size, search, category, event_date,
                                    date_from, date_to, registration_status,
                                    EventStatus(status) if status else None, upcoming_only)


@router.post("/poster", response_model=PosterOut, status_code=201)
def upload_poster(manager: Manager, file: Annotated[UploadFile, File()]):
    return {"poster_url": upload_service.upload_poster(file)}


@router.post("", response_model=EventOut, status_code=201)
def create_event(data: EventCreate, manager: Manager, db: Db):
    return event_service.event_output(db, event_service.create_event(db, manager, data))


@router.get("/{event_id}", response_model=EventOut)
def event_detail(event_id: UUID, db: Db):
    event = event_service.get_event(db, event_id)
    if event.status == EventStatus.DRAFT:
        fail(404, "EVENT_NOT_FOUND", "Event not found.")
    return event_service.event_output(db, event)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(event_id: UUID, data: EventUpdate, manager: Manager, db: Db):
    return event_service.event_output(db, event_service.update_event(db, event_id, manager, data))


@router.post("/{event_id}/publish", response_model=EventOut)
def publish_event(event_id: UUID, manager: Manager, db: Db):
    return event_service.event_output(db, event_service.publish_event(db, event_id, manager))


@router.post("/{event_id}/cancel", response_model=EventOut)
def cancel_event(event_id: UUID, manager: Manager, db: Db):
    return event_service.event_output(db, event_service.cancel_event(db, event_id, manager))


@router.post("/{event_id}/complete", response_model=EventOut)
def complete_event(event_id: UUID, manager: Manager, db: Db):
    return event_service.event_output(db, event_service.complete_event(db, event_id, manager))


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: UUID, manager: Manager, db: Db):
    event_service.delete_event(db, event_id, manager)
    return Response(status_code=204)
