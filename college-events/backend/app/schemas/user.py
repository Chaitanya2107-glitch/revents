from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, Field

from app.models.user import Role
from app.schemas.common import Input, Output


class UserOut(Output):
    id: UUID
    full_name: str
    email: str
    role: Role
    department: str | None
    academic_year: int | None
    student_id: str | None
    phone_number: str | None
    profile_image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(Input):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    department: str | None = Field(default=None, min_length=1, max_length=120)
    academic_year: int | None = Field(default=None, ge=1, le=8)
    phone_number: str | None = Field(default=None, min_length=5, max_length=32)
    profile_image_url: AnyHttpUrl | None = None
