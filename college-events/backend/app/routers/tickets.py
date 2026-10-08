from uuid import UUID

from fastapi import APIRouter, Response

from app.dependencies import CurrentUser, Db, Manager
from app.schemas.attendance import AttendanceOut
from app.schemas.ticket import TicketCheckin, TicketOut
from app.services.attendance_service import verify_checkin
from app.services.ticket_service import accessible_registration, ticket_output, ticket_pdf

router = APIRouter(prefix="/api", tags=["tickets and attendance"])


@router.get("/registrations/{registration_id}/ticket", response_model=TicketOut)
def get_ticket(registration_id: UUID, user: CurrentUser, db: Db, response: Response) -> dict:
    registration = accessible_registration(db, registration_id, user)
    response.headers["Cache-Control"] = "no-store"
    return ticket_output(db, registration, user)


@router.get("/registrations/{registration_id}/ticket/pdf", response_class=Response,
            responses={200: {"content": {"application/pdf": {}}, "description": "Downloadable entry pass"}})
def download_ticket(registration_id: UUID, user: CurrentUser, db: Db) -> Response:
    registration = accessible_registration(db, registration_id, user)
    content = ticket_pdf(db, registration, user)
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="event-pass-{registration_id}.pdf"',
        "Cache-Control": "no-store",
    })


@router.post("/tickets/verify", response_model=AttendanceOut, status_code=201)
def checkin(data: TicketCheckin, manager: Manager, db: Db) -> dict:
    attendance = verify_checkin(db, data.event_id, data.qr_token, manager)
    registration = attendance.registration
    return {
        "id": attendance.id,
        "registration_id": attendance.registration_id,
        "checked_in_at": attendance.checked_in_at,
        "checked_in_by": attendance.checked_in_by,
        "student_id": registration.student_id,
        "student_name": registration.student.full_name,
        "ticket_number": registration.ticket.ticket_number,
    }
