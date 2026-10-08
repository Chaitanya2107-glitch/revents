# Local backend setup — 2026-10-08

The existing backend is functional locally with Supabase PostgreSQL through the IPv4
session pooler. FastAPI runs at `http://127.0.0.1:8001`; port 8000 belongs to another app.

| Requested check | Result |
|---|---|
| Inspect backend and README | Done; reused existing implementation and provisioning script |
| Python dependencies | Python 3.14.5; all declared runtime/dev packages installed and compatible |
| PostgreSQL | Supabase PostgreSQL 17.11 connected through the session pooler; local PostgreSQL/Docker engine unavailable |
| Secure `.env` | Ignored `backend/.env` has independent 64-character random JWT/ticket secrets and a configured database password; psycopg driver and required SSL confirmed |
| Alembic | `0001_initial` applied; all 7 tables present |
| Initial manager | `manager@college.edu` / Event Manager created through the existing interactive script; live login and `/auth/me` pass |
| FastAPI health/docs | `/api/health`, `/docs`, `/openapi.json`: HTTP 200 on port 8001 |
| Database readiness | `/api/health/ready`: HTTP 200, status `ok` |
| Frontend contract | Live OpenAPI equals existing `backend/openapi.json`; CORS preflight from localhost:5173 passes |
| Tests | All 5 pass, including isolated real PostgreSQL API integration; temporary test database and schemas removed |
| Lint | Modified attendance service and new integration file pass; existing backend has 64 findings (line lengths, imports, ORM forward annotations) |

The session pooler connects successfully with SSL required and an 8-second connect timeout.
The direct IPv6 endpoint is unreachable from this session. The publishable API key is not
used by the backend and was not added as an unused setting.

The existing password hasher is Python `pwdlib`/Argon2. Authentication and JWTs remain
in FastAPI; only password hashes are stored in the database. Supabase Auth is not used.

## Fixes and verification

Check-in returned HTTP 500 because eager loading `Ticket → Registration → Ticket` with
`populate_existing` cleared `Ticket.registration` while its model forbids lazy loading.
The attendance service now queries the registration through the ticket and loads its
student, ticket and attendance without that cycle. Ownership, QR authentication, locks,
revocation and duplicate-scan checks remain. The regression test failed before this fix
and passes afterward. No API paths, schemas or exported contracts changed.

Supabase automatically granted `anon` and `authenticated` access to all newly created
backend tables. Those grants were revoked on the six app tables and `alembic_version`
before creating accounts. Assertions verified that both roles have no SELECT, INSERT,
UPDATE, DELETE, TRUNCATE, REFERENCES or TRIGGER privileges; FastAPI's database role keeps
access. The reproducible SQL is in the backend README. Existing migrations were preserved;
this is Supabase-specific permission setup. See [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api).

The integration test covers provisioning, signup/login/password changes, role and ownership
checks, event creation/publishing, capacity and duplicate bookings, QR PNG/PDF tickets,
tampered and wrong-event QR, attendance/duplicate scans, cancellation, seat release,
re-registration, notifications, revocation and JWT invalidation. It ran in a separate
randomly named PostgreSQL test database; all test schemas and the empty database were
removed afterward. The application database contains one manager and no test events.

One rerun encountered a transient remote connection failure; the subsequent full run
completed successfully in 20 seconds. Existing backend source files were preserved except
for the small attendance-service fix. Documentation and the integration test were updated.

## Local login and remaining actions

- Manager email: `manager@college.edu`. The generated password is in ignored
  [`.tools/manager-credentials.env`](../.tools/manager-credentials.env); it was not printed
  in the conversation or application logs. Change it through the existing password-change
  endpoint or trusted `scripts.manage reset-password` command if desired.
- Point the separate frontend API base URL at `http://localhost:8001/api`. Its allowed
  origin is `http://localhost:5173`. The placeholder college domain remains `college.edu`
  until you choose the real student email domain.
- Rotate the Supabase database password shared in chat, update `DATABASE_URL` locally
  with the new URL-encoded password, and restart FastAPI. Keep JWT/ticket secrets unchanged.

Run from `backend` after stopping the current API worker:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Current worker PID: 39408; launcher PID: 25732. Verify its command line before stopping
it because Windows can reuse PIDs. Future integration tests require `TEST_DATABASE_URL`
for a separate database named `test_*` or `*_test`; never use the app database URL.

Logs are in ignored `.tools/fastapi.stdout.log` and `.tools/fastapi.stderr.log`.
No SMTP credentials are configured; email password reset remains disabled as designed.
The existing tests emit a Starlette/httpx deprecation warning. Production load/concurrency,
SMTP delivery, comprehensive uploads/security and real-camera scanning were not tested.
