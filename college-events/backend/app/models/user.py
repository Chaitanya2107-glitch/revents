from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Index, Integer, String, column, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, IdentityMixin, TimestampMixin


class Role(StrEnum):
    STUDENT = "STUDENT"
    MANAGER = "MANAGER"


class User(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_email_ci", func.lower(column("email")), unique=True),
        CheckConstraint("email = lower(email)", name="normalized_email"),
        CheckConstraint("academic_year IS NULL OR academic_year BETWEEN 1 AND 8", name="academic_year"),
        CheckConstraint("token_version >= 0", name="token_version"),
    )

    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role", native_enum=False,
                                         create_constraint=True))
    department: Mapped[str | None] = mapped_column(String(120))
    academic_year: Mapped[int | None] = mapped_column(Integer)
    student_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    profile_image_url: Mapped[str | None] = mapped_column(String(2048))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reset_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
