# College Event Management backend

Python 3.12+ / FastAPI API for student discovery and bookings, event manager administration,
QR and PDF entry passes, attendance, notifications, and analytics. Uses PostgreSQL 15+,
SQLAlchemy 2, Alembic, Pydantic 2, psycopg, pwdlib/Argon2, PyJWT, qrcode/Pillow, and ReportLab.
The React frontend is a separate project.

Implementation is present; the backend has **not been certified for production**.
Tests cover foundation/JWT/schema behavior plus an opt-in PostgreSQL integration flow.
Concurrency, SMTP delivery, and comprehensive upload/security testing remain outstanding.

## Setup

Install Python 3.12 or newer and PostgreSQL 15 or newer. Start PostgreSQL and open a trusted
administrator `psql` session:

```sh
psql -h localhost -U postgres
```

```sql
CREATE USER college_events WITH PASSWORD 'CHOOSE_A_STRONG_LOCAL_PASSWORD';
CREATE DATABASE college_events OWNER college_events;
```

Use a separate database/account for any future test suite. Never point destructive tests at
the development or production database.

Supabase can supply PostgreSQL while FastAPI runs locally. Use the dashboard's **Connect**
dialog to obtain a direct connection URI, or a session-pooler URI on IPv4-only networks.
In `.env`, use the `postgresql+psycopg://` prefix, URL-encode the database password, and add
`sslmode=require`. See the [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).
Authentication stays in this backend: Python `pwdlib`/Argon2 hashes passwords into
`users.password_hash`; Supabase Auth and Supabase API keys are not required.
The existing migrations do not enable RLS. Supabase can automatically grant its API roles
access to new public-schema tables. After migrating a Supabase database, remove those grants
from this backend's tables before storing accounts:

```sql
REVOKE ALL ON TABLE public.users, public.events, public.registrations, public.tickets,
  public.attendance, public.notifications, public.alembic_version FROM anon, authenticated;
```

This keeps the table owner's access through FastAPI and blocks direct Data API access by
the public roles. This statement was applied and verified on the configured project.
For a dedicated backend-only project, you can also turn **Enable Data API** off in its
Data API integration settings. See [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api).

Windows PowerShell, from the repository:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux/macOS:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`: set the database password, allowed college domains, and **two different random
secrets**. Generate them locally; assign the first to `JWT_SECRET_KEY` and the second to
`TICKET_SECRET_KEY`:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))"
```

The application rejects missing or placeholder secrets. `.env` is ignored by Git; do not share it.
URL-encode special characters in database credentials. Start from the `backend` directory so
relative `.env`, upload, and Alembic paths resolve correctly.

Apply migrations, provision your first manager, and start the server on Windows:

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m scripts.manage create-manager --email manager@college.edu --full-name "Event Manager" --authorize
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Linux/macOS, with the environment activated:

```sh
python -m alembic upgrade head
python -m scripts.manage create-manager --email manager@college.edu --full-name "Event Manager" --authorize
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The manager command requires a trusted interactive terminal, database credentials, and the
explicit `--authorize` flag. It prompts twice for a password, never accepts passwords in
command-line arguments, and does not elevate existing students or create default accounts.
Operators must restrict shell and database credentials to authorized administrators.

## Configuration

All keys and defaults are in `.env.example`. Important settings:

- `DATABASE_URL`: PostgreSQL with the `postgresql+psycopg://` driver.
- `ALLOWED_COLLEGE_EMAIL_DOMAINS`: comma-separated exact domains; signup creates students only.
- `FRONTEND_ORIGIN`: defaults to `http://localhost:5173`; optional `CORS_ORIGINS` overrides it.
- `PUBLIC_BASE_URL`: absolute backend origin used for uploaded poster URLs.
- `CANCELLATION_CUTOFF_HOURS`: default 2 hours before the event starts.
- `CHECKIN_BEFORE_MINUTES` / `CHECKIN_AFTER_MINUTES`: default start minus 60 minutes through
  end plus 60 minutes, while the event remains published.
- `TICKET_PRESENTATION_TTL_MINUTES`: QR/PDF presentation lifetime, default 24 hours.
- `MAX_UPLOAD_SIZE_MB`: default 5; `MAX_IMAGE_PIXELS`: default 20 million.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: default 30. `ENVIRONMENT=production` requires HTTPS public,
  frontend, and password-reset URLs and STARTTLS when SMTP is configured.

Database sessions use UTC. Inputs must include a timezone (`Z` or an offset); responses are
ISO 8601 UTC timestamps. The frontend should format these in the viewer's local timezone.

## API reference

Base URL: `http://localhost:8000/api`. Protected endpoints accept
`Authorization: Bearer <access_token>`. Managers administer their own events only.

| Method | Path, relative to `/api` | Access / purpose |
|---|---|---|
| GET | `/health` | Public process liveness |
| GET | `/health/ready` | Database connectivity |
| POST | `/auth/register` | Public student signup |
| POST | `/auth/login` | Student/manager login |
| GET | `/auth/me` | Current authenticated account |
| POST | `/auth/change-password` | Verify old password, replace password |
| POST | `/auth/password-reset/request` | SMTP reset request |
| POST | `/auth/password-reset/confirm` | Consume single-use reset token |
| GET, PATCH | `/students/me` | Student profile |
| GET | `/events` | Public published event discovery |
| POST | `/events` | Manager creates a draft |
| POST | `/events/poster` | Manager multipart poster upload |
| GET | `/events/{event_id}` | Public event details; drafts hidden |
| PATCH | `/events/{event_id}` | Owner edits event |
| DELETE | `/events/{event_id}` | Owner deletes unbooked draft |
| POST | `/events/{event_id}/publish` | Owner publishes draft |
| POST | `/events/{event_id}/cancel` | Owner cancels published event |
| POST | `/events/{event_id}/complete` | Owner completes an ended event |
| POST | `/events/{event_id}/register` | Student books event |
| GET | `/registrations/me` | Student booking history |
| GET | `/registrations/{registration_id}` | Owning student booking detail |
| POST | `/registrations/{registration_id}/cancel` | Owning student cancellation |
| GET | `/registrations/{registration_id}/ticket` | Student QR; owner manager metadata |
| GET | `/registrations/{registration_id}/ticket/pdf` | Student pass; owner manager copy |
| POST | `/tickets/verify` | Owner manager atomic ticket check-in |
| GET | `/manager/dashboard` | Manager totals and recent activity |
| GET | `/manager/events` | Manager's drafts and event history |
| GET | `/manager/events/{event_id}/registrations` | Owner registration list |
| GET | `/manager/events/{event_id}/attendance` | Owner attendance list |
| GET | `/manager/events/{event_id}/attendance/summary` | Owner attendance totals |
| GET | `/manager/analytics` | Manager chart data |
| GET | `/notifications` | User's notifications |
| PATCH | `/notifications/{notification_id}/read` | Mark own notification read |
| PATCH | `/notifications/read-all` | Mark own notifications read |

Swagger: `http://localhost:8000/docs`. OpenAPI: `http://localhost:8000/openapi.json`.
`openapi.json` is also included as an exported frontend contract. Regenerate after API edits:

```sh
python -m scripts.export_openapi
```

Lists use `page=1&page_size=20`, with a maximum page size of 100:

```json
{"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0}
```

Event filters: `search`, `category`, `date=YYYY-MM-DD` (UTC day), timezone-aware
`date_from`/`date_to`, `registration_status=OPEN|CLOSED|FULL`, `upcoming_only=true`, and
`status=PUBLISHED|CANCELLED|COMPLETED`. Default discovery returns published events, sorted by
start time. Booking history uses `period=upcoming|past|cancelled`. Manager registration filters
use `status=confirmed|cancelled|checked_in|not_checked_in`. Notification filters use `is_read`.
Analytics per-event charts are paginated and date trends accept `trend_days` (1–366).
Attendance rates are percentages of confirmed bookings; historical check-ins remain available
separately as `total_check_ins`. Empty trend days are omitted; a frontend may fill them with zero.

Errors have a consistent shape; validation errors additionally contain sanitized field errors:

```json
{"detail": {"code": "EVENT_FULL", "message": "Registration is closed because the event is full."}}
```

## Frontend requests

Student signup (`POST /auth/register`):

```json
{"full_name":"Rahul Sharma","email":"rahul@college.edu","password":"UseAUniquePassword123!","department":"Computer Science","academic_year":2,"student_id":"CS2026001"}
```

Login (`POST /auth/login`) uses JSON for both roles:

```json
{"email":"rahul@college.edu","password":"UseAUniquePassword123!"}
```

Response contains `access_token`, `token_type`, `user`, and `role` (`STUDENT` or `MANAGER`).
Use a manager's provisioned credentials for manager requests; signup cannot select a role.
Passwords require 12–128 characters. Email addresses are normalized. Do not render event
descriptions as unsanitized HTML or persist access tokens in URLs.

React/Vite example helper and the requested flows:

```typescript
const API = "http://localhost:8000/api";
async function api(path: string, token?: string, method = "GET", body?: unknown) {
  const response = await fetch(API + path, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail?.message ?? "Request failed");
  return data;
}

const session = await api("/auth/login", undefined, "POST", {
  email: "rahul@college.edu", password: "UseAUniquePassword123!",
});
const user = await api("/auth/me", session.access_token);
const events = await api("/events?upcoming_only=true&registration_status=OPEN");
const booking = await api(`/events/${eventId}/register`, session.access_token, "POST");
const ticket = await api(`/registrations/${booking.id}/ticket`, session.access_token);
// Display ticket.qr_image_data_url in an <img>; refresh when qr_expires_at approaches.

const event = await api("/events", managerToken, "POST", {
  title: "CodeFest 2026", description: "College coding competition",
  category: "Technical", venue: "Main Auditorium", capacity: 100,
  start_time: "2026-11-10T09:00:00+05:30",
  end_time: "2026-11-10T17:00:00+05:30",
  registration_deadline: "2026-11-09T18:00:00+05:30",
}); // Use future dates when running this example.
await api(`/events/${event.id}/publish`, managerToken, "POST");
const attendance = await api("/tickets/verify", managerToken, "POST", {
  event_id: event.id, qr_token: scannedQrText,
});
```

The check-in body is JSON:

```json
{"event_id":"EVENT_UUID","qr_token":"OPAQUE_SCANNED_QR_TEXT"}
```

PDF downloads and multipart uploads require separate fetch handling:

```typescript
const pdfResponse = await fetch(`${API}/registrations/${booking.id}/ticket/pdf`, {
  headers: { Authorization: `Bearer ${session.access_token}` },
});
if (!pdfResponse.ok) throw new Error("PDF download failed");
const downloadUrl = URL.createObjectURL(await pdfResponse.blob());
const link = document.createElement("a");
link.href = downloadUrl; link.download = "event-pass.pdf"; link.click();
setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);

const form = new FormData(); form.append("file", posterFile);
const upload = await fetch(`${API}/events/poster`, {
  method: "POST", headers: { Authorization: `Bearer ${managerToken}` }, body: form,
}); // Let the browser set the multipart Content-Type/boundary.
if (!upload.ok) throw new Error("Poster upload failed");
const { poster_url } = await upload.json(); // Include in event creation or PATCH.
```

## Booking and ticket policies

Registration, capacity checks, ticket issuance, and confirmation notifications share one
database transaction. Event row locks serialize booking, cancellation, capacity edits, and
check-in. PostgreSQL also enforces one confirmed booking per student/event, one ticket per
registration, and one attendance record per registration. Sessions commit before HTTP success
responses are sent. Direct database writers must observe the same locking protocol.

Students may cancel before the configured cutoff, unless already checked in. Tickets are
revoked and seats released. Re-registering creates a **new registration and ticket**; earlier
cancelled records remain visible. Event cancellation preserves all booking and attendance
history and revokes associated tickets. Only unbooked drafts can be deleted. Schedule and
registration deadline become immutable after any booking; other details may change before
start, with student notifications. Capacity cannot fall below the confirmed booking count.

QR payloads contain an opaque ticket identifier, expiry, and HMAC credentials/signature.
They contain no student details, passwords, or authentication JWTs. A random UUID plus an
independent secret produces an unpredictable credential; only its SHA-256 hash is stored.
The server can rederive it to produce a new signed presentation without permanently storing
plaintext credentials. Only the owning student receives the QR token/image. Owner managers
can obtain metadata and a PDF copy without QR credentials.

QR presentations expire after 24 hours by default, including those in downloaded PDFs.
Retrieve/download again near the event. The frontend's scanner sends the exact decoded QR
string with the selected event ID and the manager's bearer token. Verification checks manager
ownership, signature, expiry, credential hash, event match, registration, revocation, entry
window, and existing attendance. A duplicate successful scan returns `409 ALREADY_CHECKED_IN`.
Rotating `TICKET_SECRET_KEY` invalidates existing credentials; preserve it across ordinary
restarts and plan a controlled reissue process before rotation. The simple PDF font may replace
characters outside Western scripts; embed a Unicode font when that is required.

## Password reset, uploads, and deployment notes

Password changes and resets increment a token version, immediately invalidating prior access
tokens. Configure SMTP for email reset. Without `SMTP_HOST`/`SMTP_FROM_EMAIL`, requests return
`503 RESET_UNAVAILABLE` and do not claim to send mail. Reset tokens are random, hashed in the
database, expire, and are consumed once. An authorized operator can reset an account locally:

```sh
python -m scripts.manage reset-password --email rahul@college.edu --authorize
```

The local auth limiter bounds signup/login/reset attempts per client IP and process. Before
multiple workers or production deployment, enforce a shared rate limit at your API gateway or
reverse proxy. Trust forwarded IP headers only from your configured proxy. Use HTTPS, restricted
database credentials, backups, a persistent upload volume, and secret storage for deployment.
Configure a proxy request-body limit to complement application upload limits.

Poster content must decode as JPEG, PNG, or WebP. Size and pixel limits apply; decoded pixels
are re-encoded to WebP with a random filename, stripping metadata and appended content.
Local development serves `/uploads`. To use cloud storage, replace the final persistence step
in `upload_service.py` with an object-storage write and return that object's public/CDN URL.
Old/orphaned uploads are not automatically garbage-collected.

## Files and future verification

```text
backend/
  app/
    main.py config.py database.py dependencies.py security.py errors.py
    models/       user event registration ticket attendance notification
    schemas/      auth user event registration ticket attendance notification manager common
    routers/      auth students events registrations tickets managers notifications
    services/     auth_service event_service registration_service ticket_service attendance_service upload_service
  alembic/        env.py script.py.mako versions/0001_initial.py
  scripts/        manage.py export_openapi.py
  tests/          foundation/security and opt-in PostgreSQL integration tests
  uploads/        local poster storage
  .env.example .gitignore alembic.ini pyproject.toml requirements.txt openapi.json
```

From `backend`, run `.venv\Scripts\python.exe -m pytest -p no:cacheprovider`.
The PostgreSQL integration test skips unless `TEST_DATABASE_URL` is explicitly set to a
separate database whose name starts with `test_` or ends with `_test`. It applies Alembic in
a generated schema, exercises manager provisioning, authentication, event publishing,
registration, QR/PDF tickets, attendance, cancellation and token invalidation, then removes
only that schema. Never reuse the application database URL for these tests.
Supabase's default database name `postgres` is intentionally rejected by this test guard;
use a separate PostgreSQL test database, for example `college_events_test`.

Ruff is available with `.venv\Scripts\python.exe -m ruff check . --no-cache`.
Migration round trips, last-seat concurrency, scan/cancel races, SMTP delivery,
comprehensive uploads/security, QR expiry, analytics, and CORS still need verification.
The optional development seed script and production storage/gateway provisioning were omitted.
See [the local setup report](../docs/local-backend-status.md) for checks and outstanding actions.

Troubleshooting: connection failures usually mean PostgreSQL is stopped or `DATABASE_URL`
is wrong; missing tables mean migrations were not applied; startup validation errors mean
secrets/URLs are invalid; `COLLEGE_EMAIL_REQUIRED` means the configured college domain differs;
drafts appear only in the manager list; reset is unavailable until SMTP is configured; expired
QR passes must be refreshed. The selected API port must be free and the frontend origin must
exactly match CORS configuration. If port 8000 is occupied, use `--port 8001`, set
`PUBLIC_BASE_URL=http://localhost:8001`, and configure the frontend API base URL accordingly.
