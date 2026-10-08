# College Events Backend Implementation Plan

Execution update: the user explicitly changed priority to implementation speed. Finish all
features first; defer tests, linting, comprehensive test writing, and extensive auditing until
requested. Independent event, ticket/attendance, and manager/notification modules were
implemented in parallel. Dependencies installed and OpenAPI exported; no PostgreSQL database
was initialized and no verification suite was run for the completed features. See
backend/IMPLEMENTATION_REPORT.md for the delivered state.

Goal: implement the user's complete backend specification, with PostgreSQL integration tests.
Architecture: synchronous FastAPI routes, SQLAlchemy sessions committed before responses,
small domain services, PostgreSQL row locks and constraints. No frontend or worker services.
Stack: Python 3.12+, FastAPI, PostgreSQL/psycopg, SQLAlchemy 2, Alembic, Pydantic 2,
pwdlib Argon2, PyJWT, qrcode/Pillow, ReportLab, pytest/HTTPX, Ruff.

Scope: app configuration/dependencies, six domain models, input/output schemas, routers,
five domain services, migrations, trusted-local administration CLI, tests, uploads,
environment example, OpenAPI export, README and implementation report.

1. Foundation: health/OpenAPI test first; configure project, settings, session lifecycle,
   consistent errors and CORS. Install dependencies. Establish isolated PostgreSQL testing.
2. Authentication: tests for signup/login/role escalation, then users, JWT/password handling,
   protected dependencies, password reset and trusted-local manager provisioning.
3. Events: tests for ownership/publication/validation, then create/edit/publish/cancel/delete,
   paginated discovery with counts. Re-test authentication and events.
4. Registrations: success/duplicates/capacity/deadline/cancellation/concurrency tests first;
   event row lock serializes registration, edits, cancellation and check-in. Partial unique
   index protects confirmed bookings; cancelled records remain and re-booking creates a new one.
5. Tickets: tests for QR/PDF, uniqueness and rejection first; HMAC-derived secret stored only
   as a hash, signed expiring presentation tokens, owner-only QR, owner manager metadata/PDF.
6. Attendance: tests for replay/wrong event/owner/window/revocation, then atomic check-in,
   immutable attendance and summaries. Managers own their events; no implicit global access.
7. Notifications/analytics/uploads: tests for scoping/counts/read state and malicious uploads,
   then paginated REST notifications and manager-scoped chart data and verified poster storage.
8. Integration: full pytest/Ruff/migration round-trip/Alembic drift/CORS/OpenAPI checks;
   fresh code review, fix findings, document setup, frontend JSON examples and limitations.

Policies: schedule/deadline locked after any booking; completed or elapsed events immutable;
capacity cannot shrink below confirmed count. Cancellation cutoff defaults to 2h before start,
check-in from 1h before start until end + 1h. QR presentation lasts 24h and can be refreshed.
Password changes/reset invalidate access tokens using a user token version. SMTP reset is
explicitly unavailable without configured delivery. Local auth limiter is per process;
production needs gateway limiting across workers. Test database isolation must fail closed.

Review focus: concurrent last-seat bookings; concurrent scan/cancel; explicit null/naive dates;
manager and student object access; malformed/expired/tampered tokens and image content.

Execution: native in this session, as requested; no approval pauses. No existing git repo.
