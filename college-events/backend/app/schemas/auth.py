from pydantic import EmailStr, Field, SecretStr, field_validator

from app.models import Role
from app.schemas.common import Input
from app.schemas.user import UserOut


class Credentials(Input):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value


class Signup(Credentials):
    full_name: str = Field(min_length=2, max_length=120)
    password: SecretStr = Field(min_length=12, max_length=128)
    department: str | None = Field(default=None, min_length=1, max_length=120)
    academic_year: int | None = Field(default=None, ge=1, le=8)
    student_id: str | None = Field(default=None, min_length=1, max_length=64)
    phone_number: str | None = Field(default=None, min_length=5, max_length=32)
    role: Role | None = None


class LoginResponse(Input):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    role: Role


class ChangePassword(Input):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class ResetRequest(Input):
    email: EmailStr


class ResetPassword(Input):
    token: str = Field(min_length=32, max_length=256)
    new_password: SecretStr = Field(min_length=12, max_length=128)
