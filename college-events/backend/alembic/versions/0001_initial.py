"""Users, events, bookings, tickets, attendance and notifications.

Revision ID: 0001_initial
Revises: None
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("STUDENT", "MANAGER", name="user_role", native_enum=False,
                                  create_constraint=True), nullable=False),
        sa.Column("department", sa.String(120)),
        sa.Column("academic_year", sa.Integer()),
        sa.Column("student_id", sa.String(64)),
        sa.Column("phone_number", sa.String(32)),
        sa.Column("profile_image_url", sa.String(2048)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reset_token_hash", sa.String(64)),
        sa.Column("reset_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("student_id", name=op.f("uq_users_student_id")),
        sa.UniqueConstraint("reset_token_hash", name=op.f("uq_users_reset_token_hash")),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_normalized_email")),
        sa.CheckConstraint("academic_year IS NULL OR academic_year BETWEEN 1 AND 8",
                           name=op.f("ck_users_academic_year")),
        sa.CheckConstraint("token_version >= 0", name=op.f("ck_users_token_version")),
    )
    op.create_index("uq_users_email_ci", "users", [sa.text("lower(email)")], unique=True)
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("poster_url", sa.String(2048)),
        sa.Column("venue", sa.String(200), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("eligibility", sa.Text()),
        sa.Column("rules", sa.Text()),
        sa.Column("organizer_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "PUBLISHED", "CANCELLED", "COMPLETED",
                                    name="event_status", native_enum=False, create_constraint=True),
                  nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
        sa.UniqueConstraint("slug", name=op.f("uq_events_slug")),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_events_organizer_id_users")),
        sa.CheckConstraint("capacity > 0", name=op.f("ck_events_positive_capacity")),
        sa.CheckConstraint("end_time > start_time", name=op.f("ck_events_valid_dates")),
        sa.CheckConstraint("registration_deadline <= start_time", name=op.f("ck_events_valid_deadline")),
    )
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"])
    op.create_index("ix_events_status_start_time", "events", ["status", "start_time"])
    op.create_index("ix_events_category_start_time", "events", ["category", "start_time"])
    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("CONFIRMED", "CANCELLED", name="registration_status",
                                    native_enum=False, create_constraint=True),
                  nullable=False, server_default="CONFIRMED"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_registrations")),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_registrations_student_id_users")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="RESTRICT",
                                name=op.f("fk_registrations_event_id_events")),
        sa.CheckConstraint("(status = 'CONFIRMED' AND cancelled_at IS NULL) OR "
                           "(status = 'CANCELLED' AND cancelled_at IS NOT NULL)",
                           name=op.f("ck_registrations_cancellation_state")),
    )
    op.create_index("uq_registrations_confirmed_student_event", "registrations",
                    ["student_id", "event_id"], unique=True,
                    postgresql_where=sa.text("status = 'CONFIRMED'"))
    op.create_index("ix_registrations_event_status", "registrations", ["event_id", "status"])
    op.create_index("ix_registrations_student_registered_at", "registrations",
                    ["student_id", "registered_at"])
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_number", sa.String(40), nullable=False),
        sa.Column("qr_token_hash", sa.String(64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="RESTRICT",
                                name=op.f("fk_tickets_registration_id_registrations")),
        sa.UniqueConstraint("registration_id", name=op.f("uq_tickets_registration_id")),
        sa.UniqueConstraint("ticket_number", name=op.f("uq_tickets_ticket_number")),
        sa.UniqueConstraint("qr_token_hash", name=op.f("uq_tickets_qr_token_hash")),
    )
    op.create_table(
        "attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked_in_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attendance")),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="RESTRICT",
                                name=op.f("fk_attendance_registration_id_registrations")),
        sa.ForeignKeyConstraint(["checked_in_by"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_attendance_checked_in_by_users")),
        sa.UniqueConstraint("registration_id", name=op.f("uq_attendance_registration_id")),
    )
    op.create_index("ix_attendance_checked_in_at", "attendance", ["checked_in_at"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.Enum("BOOKING_CONFIRMED", "BOOKING_CANCELLED", "EVENT_CANCELLED",
                                  "EVENT_UPDATED", name="notification_type", native_enum=False,
                                  create_constraint=True), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT",
                                name=op.f("fk_notifications_user_id_users")),
    )
    op.create_index("ix_notifications_user_read_created", "notifications",
                    ["user_id", "is_read", "created_at"])


def downgrade() -> None:
    for table in ("notifications", "attendance", "tickets", "registrations", "events", "users"):
        op.drop_table(table)

