# Implementation report

Implemented source:

- JWT authentication for students/managers, Argon2 password hashing, public student-only signup,
  current-user/profile endpoints, password change, SMTP password reset, and trusted-local
  manager provisioning/password reset.
- Six PostgreSQL models, foreign keys/check constraints/indexes, confirmed-booking partial
  uniqueness, unique tickets and attendance, and explicit Alembic initial migration.
- Draft creation, owner editing, publication, cancellation, completion, safe draft deletion,
  search/filter/pagination, available-seat counts, and verified poster uploads.
- Transactional bookings, deadline/capacity enforcement, cancellation, re-booking, and history.
- Expiring opaque QR presentations, hashed stored credentials, owner-only QR disclosure,
  downloadable PDF passes, manager check-in, immutable attendance records and summaries.
- User-scoped REST notifications and manager-scoped dashboard/chart analytics.
- Environment example, dependency configuration, exported OpenAPI, Swagger, and setup/frontend
  documentation.

Status and limitations:

- The user requested implementation speed and explicitly deferred tests/linting. No completed
  backend test suite was run. The initial foundation/JWT tests predate the remaining features
  and do not establish end-to-end correctness. Comprehensive integration tests are not written.
- Python dependencies were installed successfully in `backend/.venv` using Python 3.14.5.
  The terminal/network restriction encountered earlier was lifted. PostgreSQL was not installed
  and Docker was not running; no database was created and migrations were not applied.
- OpenAPI was generated from the connected routers without a database connection. This is
  contract generation, not an API/database functional test.
- SMTP must be configured for email reset; otherwise the API reports its unavailability.
- QR/PDF presentations expire (default 24h). Ticket-key rotation requires controlled reissue.
  PDF font coverage is limited, and local posters need persistent storage in deployment.
- Auth rate limiting is per process; deploy a gateway limit before scaling to multiple workers.
- Optional seed data, cloud storage integration, production provisioning, and automatic upload
  cleanup are omitted. All requested core API areas have source implementations, but runtime
  correctness and production readiness remain unverified.

See README.md for the full endpoint list, files, database setup, and Windows/Linux commands.
