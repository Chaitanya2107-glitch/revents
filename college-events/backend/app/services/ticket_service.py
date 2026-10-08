import base64
import hashlib
import hmac
import re
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID, uuid4
from xml.sax.saxutils import escape

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import utcnow
from app.errors import fail
from app.models import EventStatus, Registration, RegistrationStatus, Role, Ticket, User

TOKEN_PATTERN = re.compile(
    r"ct1\.([0-9a-f]{32})\.([1-9][0-9]{0,9})\.([A-Za-z0-9_-]{43})\.([A-Za-z0-9_-]{43})"
)


def _mac(value: bytes) -> bytes:
    return hmac.digest(get_settings().ticket_secret_key.get_secret_value().encode(), value, "sha256")


def _encoded(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _credential(ticket_id: UUID) -> bytes:
    return _mac(b"ticket-credential:" + ticket_id.bytes)


def issue_ticket(db: Session, registration: Registration) -> Ticket:
    if registration.id is None:
        db.flush()
    ticket_id = uuid4()
    ticket = Ticket(
        id=ticket_id,
        registration_id=registration.id,
        ticket_number="CE-" + uuid4().hex.upper(),
        qr_token_hash=hashlib.sha256(_credential(ticket_id)).hexdigest(),
        issued_at=utcnow(),
    )
    db.add(ticket)
    db.flush()
    return ticket


def presentation_token(ticket: Ticket) -> tuple[str, datetime]:
    expires_at = utcnow() + timedelta(minutes=get_settings().ticket_presentation_ttl_minutes)
    expiry = int(expires_at.timestamp())
    credential = _credential(ticket.id)
    if not hmac.compare_digest(hashlib.sha256(credential).hexdigest(), ticket.qr_token_hash):
        fail(409, "TICKET_KEY_CHANGED", "Ticket credentials are unavailable. Contact the event organizer.")
    payload = f"ct1.{ticket.id.hex}.{expiry}.{_encoded(credential)}"
    signature = _encoded(_mac(b"ticket-presentation:" + payload.encode("ascii")))
    return f"{payload}.{signature}", datetime.fromtimestamp(expiry, UTC)


def parse_presentation_token(token: str) -> tuple[UUID, str]:
    match = TOKEN_PATTERN.fullmatch(token)
    if match is None:
        fail(400, "INVALID_QR", "The QR ticket is invalid.")
    ticket_hex, expiry, credential_text, signature = match.groups()
    payload = token.rsplit(".", 1)[0]
    expected_signature = _encoded(_mac(b"ticket-presentation:" + payload.encode("ascii")))
    if not hmac.compare_digest(signature, expected_signature):
        fail(400, "INVALID_QR", "The QR ticket is invalid.")
    if int(expiry) <= int(utcnow().timestamp()):
        fail(400, "EXPIRED_QR", "This QR ticket has expired. Refresh the ticket before scanning.")
    ticket_id = UUID(hex=ticket_hex)
    expected_credential = _credential(ticket_id)
    if not hmac.compare_digest(credential_text, _encoded(expected_credential)):
        fail(400, "INVALID_QR", "The QR ticket is invalid.")
    return ticket_id, hashlib.sha256(expected_credential).hexdigest()


def _qr_png(token: str) -> bytes:
    image = qrcode.make(token, box_size=8, border=4)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def accessible_registration(db: Session, registration_id: UUID, viewer: User) -> Registration:
    registration = db.scalar(
        select(Registration)
        .where(Registration.id == registration_id)
        .options(
            selectinload(Registration.event),
            selectinload(Registration.student),
            selectinload(Registration.ticket),
        )
        .execution_options(populate_existing=True)
    )
    if registration is None:
        fail(404, "REGISTRATION_NOT_FOUND", "Registration not found.")
    owner = viewer.role == Role.STUDENT and registration.student_id == viewer.id
    manager = viewer.role == Role.MANAGER and registration.event.organizer_id == viewer.id
    if not owner and not manager:
        fail(403, "FORBIDDEN", "You cannot access this registration.")
    return registration


def ticket_output(db: Session, registration: Registration, viewer: User) -> dict:
    registration = accessible_registration(db, registration.id, viewer)
    ticket = registration.ticket
    if ticket is None:
        fail(404, "TICKET_NOT_FOUND", "Ticket not found.")
    event = registration.event
    output = {
        "id": ticket.id,
        "registration_id": registration.id,
        "event_id": event.id,
        "ticket_number": ticket.ticket_number,
        "app_name": get_settings().app_name,
        "event_title": event.title,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "venue": event.venue,
        "student_name": registration.student.full_name,
        "status": registration.status,
        "issued_at": ticket.issued_at,
        "revoked_at": ticket.revoked_at,
        "qr_token": None,
        "qr_image_data_url": None,
        "qr_expires_at": None,
    }
    if (viewer.role == Role.STUDENT and registration.status == RegistrationStatus.CONFIRMED
            and ticket.revoked_at is None and event.status == EventStatus.PUBLISHED):
        token, expiry = presentation_token(ticket)
        output.update(
            qr_token=token,
            qr_expires_at=expiry,
            qr_image_data_url="data:image/png;base64," + base64.b64encode(_qr_png(token)).decode("ascii"),
        )
    return output


def ticket_pdf(db: Session, registration: Registration, viewer: User) -> bytes:
    output = ticket_output(db, registration, viewer)
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles["Normal"].textColor = colors.HexColor("#222222")
    styles["Normal"].leading = 16

    def text(value: object) -> str:
        # ponytail: Helvetica cannot render every script; embed a Unicode font when required.
        return escape(str(value).encode("cp1252", "replace").decode("cp1252")).replace("\n", "<br/>")

    story = [Paragraph(text(output["app_name"]), styles["Title"]), Spacer(1, 0.15 * inch),
             Paragraph(text(output["event_title"]), styles["Heading1"]), Spacer(1, 0.15 * inch)]
    for label, value in (
        ("Student", output["student_name"]),
        ("Ticket number", output["ticket_number"]),
        ("Starts (UTC)", output["start_time"].astimezone(UTC).strftime("%d %B %Y, %H:%M")),
        ("Ends (UTC)", output["end_time"].astimezone(UTC).strftime("%d %B %Y, %H:%M")),
        ("Venue", output["venue"]),
        ("Registration", output["status"].value),
    ):
        story.extend([Paragraph(f"<b>{label}:</b> {text(value)}", styles["Normal"]), Spacer(1, 0.08 * inch)])
    if output["qr_token"] is not None:
        story.extend([
            Spacer(1, 0.2 * inch),
            Image(BytesIO(_qr_png(output["qr_token"])), width=2.5 * inch, height=2.5 * inch),
            Spacer(1, 0.15 * inch),
            Paragraph("QR valid until " + text(output["qr_expires_at"].isoformat()) +
                      ". Download a new pass if this expires before your event.", styles["Normal"]),
        ])
    else:
        message = "Organizer copy: QR credentials are available only to the registered student."
        if output["revoked_at"] is not None or output["status"] != RegistrationStatus.CONFIRMED:
            message = "This ticket is revoked and cannot be used for entry."
        story.extend([Spacer(1, 0.15 * inch), Paragraph(message, styles["Normal"])])
    SimpleDocTemplate(buffer, pagesize=A4, title="Event entry pass",
                      leftMargin=0.7 * inch, rightMargin=0.7 * inch).build(story)
    return buffer.getvalue()
