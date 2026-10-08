"""Opt-in critical flows against an isolated schema in a separate PostgreSQL test DB."""
import base64
import os
import re
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from alembic import command


@pytest.fixture
def postgres_client(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a separate PostgreSQL test database.")
    url = make_url(database_url)
    if url.drivername != "postgresql+psycopg" or not (
        (url.database or "").startswith("test_") or (url.database or "").endswith("_test")
    ):
        pytest.fail("TEST_DATABASE_URL must use psycopg and a database named test_* or *_test.")
    schema = "test_college_events_" + uuid4().hex
    engine = create_engine(database_url, connect_args={
        "options": f"-c search_path={schema} -c timezone=UTC "
                   "-c statement_timeout=15000 -c lock_timeout=5000",
    })
    created = False
    try:
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        created = True
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

        from app import dependencies, main
        from app.config import get_settings
        from app.database import get_db
        from app.security import AuthRateLimiter
        from scripts import manage

        settings = get_settings()
        monkeypatch.setattr(settings, "allowed_college_email_domains", "college.edu")
        monkeypatch.setattr(settings, "checkin_before_minutes", 60)
        monkeypatch.setattr(settings, "checkin_after_minutes", 60)
        monkeypatch.setattr(settings, "cancellation_cutoff_hours", 2)

        @lru_cache
        def test_engine():
            return engine

        def test_db():
            with Session(engine, expire_on_commit=False, autoflush=False) as db:
                try:
                    yield db
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

        monkeypatch.setattr(main, "get_engine", test_engine)
        monkeypatch.setattr(manage, "get_engine", test_engine)
        monkeypatch.setattr(dependencies, "auth_limiter", AuthRateLimiter(20, 60))
        overrides = main.app.dependency_overrides.copy()
        main.app.dependency_overrides[get_db] = test_db
        try:
            with TestClient(main.app) as client:
                yield client
        finally:
            main.app.dependency_overrides.clear()
            main.app.dependency_overrides.update(overrides)
    finally:
        try:
            if created:
                assert re.fullmatch(r"test_college_events_[0-9a-f]{32}", schema)
                with engine.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
        finally:
            engine.dispose()


def test_authentication_booking_ticket_and_attendance(postgres_client, monkeypatch):
    """Catch broken migrations, role/ownership checks, seat release and QR revocation."""
    from scripts import manage

    client = postgres_client
    password = "Integration-Password-123!"

    def request(method, path, token=None, status=200, **kwargs):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = client.request(method, "/api" + path, headers=headers, **kwargs)
        assert response.status_code == status, response.text
        return response

    def error(method, path, token, status, code, **kwargs):
        assert request(method, path, token, status, **kwargs).json()["detail"]["code"] == code

    def login(email, login_password=password):
        return request("POST", "/auth/login", json={
            "email": email, "password": login_password,
        }).json()

    for email in ("manager@college.edu", "other-manager@college.edu"):
        with monkeypatch.context() as provision:
            provision.setattr(manage.sys.stdin, "isatty", lambda: True)
            provision.setattr(manage.getpass, "getpass", lambda prompt: password)
            provision.setattr(manage.sys, "argv", [
                "manage", "create-manager", "--email", email,
                "--full-name", "Integration Manager", "--authorize",
            ])
            assert manage.main() == 0
    manager_session = login("manager@college.edu")
    assert manager_session["role"] == "MANAGER"
    manager = manager_session["access_token"]
    other_manager = login("other-manager@college.edu")["access_token"]
    student_data = {"full_name": "Integration Student", "email": "student@college.edu",
                    "password": password, "department": "Computer Science", "academic_year": 2}
    signed_up = request("POST", "/auth/register", status=201, json=student_data).json()
    assert signed_up["role"] == "STUDENT"
    request("POST", "/auth/register", status=201,
            json={**student_data, "email": "other-student@college.edu"})
    error("POST", "/auth/register", None, 409, "ACCOUNT_EXISTS", json=student_data)
    error("POST", "/auth/register", None, 422, "VALIDATION_ERROR",
          json={**student_data, "role": "MANAGER"})
    error("POST", "/auth/login", None, 401, "INVALID_CREDENTIALS",
          json={"email": student_data["email"], "password": "incorrect"})
    student_session = login(student_data["email"])
    assert student_session["role"] == "STUDENT"
    student = student_session["access_token"]
    other_student = login("other-student@college.edu")["access_token"]
    assert request("GET", "/auth/me", student).json()["id"] == student_session["user"]["id"]
    error("GET", "/auth/me", None, 401, "AUTH_REQUIRED")
    assert request("GET", "/health/ready").json() == {"status": "ok"}

    now = datetime.now(UTC)
    event_data = {"title": "Integration Event", "description": "Local integration verification",
                  "category": "Technical", "venue": "Test Auditorium", "capacity": 1,
                  "start_time": (now + timedelta(minutes=30)).isoformat(),
                  "end_time": (now + timedelta(minutes=90)).isoformat(),
                  "registration_deadline": (now + timedelta(minutes=15)).isoformat()}
    error("POST", "/events", student, 403, "MANAGER_REQUIRED", json=event_data)
    event = request("POST", "/events", manager, 201, json=event_data).json()
    event_path = f"/events/{event['id']}"
    assert event["status"] == "DRAFT"
    error("GET", event_path, None, 404, "EVENT_NOT_FOUND")
    assert request("POST", event_path + "/publish", manager).json()["status"] == "PUBLISHED"
    assert request("GET", "/events").json()["items"][0]["id"] == event["id"]
    error("POST", event_path + "/register", manager, 403, "STUDENT_REQUIRED")
    booking = request("POST", event_path + "/register", student, 201).json()
    assert booking["status"] == "CONFIRMED" and booking["ticket"]["ticket_number"]
    error("POST", event_path + "/register", student, 409, "ALREADY_REGISTERED")
    error("POST", event_path + "/register", other_student, 409, "EVENT_FULL")
    ticket_path = f"/registrations/{booking['id']}/ticket"
    error("GET", ticket_path, other_student, 403, "FORBIDDEN")
    ticket = request("GET", ticket_path, student).json()
    assert ticket["qr_token"] and ticket["qr_expires_at"]
    prefix, png = ticket["qr_image_data_url"].split(",", 1)
    assert prefix == "data:image/png;base64"
    with Image.open(BytesIO(base64.b64decode(png))) as image:
        assert image.format == "PNG" and image.width == image.height
        image.verify()
    assert request("GET", ticket_path, manager).json()["qr_token"] is None
    pdf = request("GET", ticket_path + "/pdf", student)
    assert pdf.headers["content-type"] == "application/pdf" and pdf.content.startswith(b"%PDF-")
    assert pdf.headers["cache-control"] == "no-store"
    qr = {"event_id": event["id"], "qr_token": ticket["qr_token"]}
    error("POST", "/tickets/verify", other_manager, 403, "EVENT_FORBIDDEN", json=qr)
    altered = ticket["qr_token"][:-1] + ("A" if ticket["qr_token"][-1] != "A" else "B")
    error("POST", "/tickets/verify", manager, 400, "INVALID_QR", json={**qr, "qr_token": altered})
    attendance = request("POST", "/tickets/verify", manager, 201, json=qr).json()
    assert attendance["registration_id"] == booking["id"]
    error("POST", "/tickets/verify", manager, 409, "ALREADY_CHECKED_IN", json=qr)
    error("POST", f"/registrations/{booking['id']}/cancel", student, 409, "ALREADY_CHECKED_IN")
    assert request("GET", f"/registrations/{booking['id']}", student).json()["checked_in"] is True
    manager_path = f"/manager/events/{event['id']}/attendance"
    assert request("GET", manager_path, manager).json()["total"] == 1
    summary = request("GET", manager_path + "/summary", manager).json()
    assert summary["attended"] == summary["total_confirmed"] == summary["total_check_ins"] == 1
    assert summary["not_yet_checked_in"] == 0

    future_data = {**event_data, "title": "Cancellation Event",
                   "start_time": (now + timedelta(hours=3)).isoformat(),
                   "end_time": (now + timedelta(hours=4)).isoformat(),
                   "registration_deadline": (now + timedelta(hours=2)).isoformat()}
    future = request("POST", "/events", manager, 201, json=future_data).json()
    future_path = f"/events/{future['id']}"
    request("POST", future_path + "/publish", manager)
    error("POST", "/tickets/verify", manager, 400, "WRONG_EVENT",
          json={**qr, "event_id": future["id"]})
    cancelled = request("POST", future_path + "/register", student, 201).json()
    cancelled_path = f"/registrations/{cancelled['id']}"
    cancelled_ticket = request("GET", cancelled_path + "/ticket", student).json()
    cancelled_qr = {"event_id": future["id"], "qr_token": cancelled_ticket["qr_token"]}
    error("POST", "/tickets/verify", manager, 409, "CHECKIN_CLOSED", json=cancelled_qr)
    assert request("POST", cancelled_path + "/cancel", student).json()["status"] == "CANCELLED"
    error("POST", "/tickets/verify", manager, 409, "REVOKED_TICKET", json=cancelled_qr)
    assert request("GET", cancelled_path + "/ticket", student).json()["qr_token"] is None
    replacement = request("POST", future_path + "/register", student, 201).json()
    assert replacement["id"] != cancelled["id"]
    assert replacement["ticket"]["id"] != cancelled["ticket"]["id"]
    replacement_path = f"/registrations/{replacement['id']}"
    replacement_ticket = request("GET", replacement_path + "/ticket", student).json()
    request("PATCH", future_path, manager, json={"venue": "Updated Auditorium"})
    assert request("POST", future_path + "/cancel", manager).json()["status"] == "CANCELLED"
    error("POST", "/tickets/verify", manager, 409, "REVOKED_TICKET", json={
        "event_id": future["id"], "qr_token": replacement_ticket["qr_token"],
    })
    assert request("GET", replacement_path, student).json()["status"] == "CANCELLED"
    notifications = request("GET", "/notifications", student).json()["items"]
    assert {"EVENT_UPDATED", "EVENT_CANCELLED"} <= {item["type"] for item in notifications}

    changed_password = "Changed-Integration-Password-123!"
    request("POST", "/auth/change-password", student, json={
        "current_password": password, "new_password": changed_password,
    })
    error("GET", "/auth/me", student, 401, "INVALID_TOKEN")
    assert login(student_data["email"], changed_password)["role"] == "STUDENT"
