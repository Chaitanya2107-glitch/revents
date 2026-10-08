from fastapi import APIRouter

from app.dependencies import Db, Student
from app.errors import fail
from app.schemas.user import ProfileUpdate, UserOut

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/me", response_model=UserOut)
def profile(user: Student):
    return user


@router.patch("/me", response_model=UserOut)
def update_profile(data: ProfileUpdate, user: Student, db: Db):
    values = data.model_dump(exclude_unset=True, mode="json")
    if "full_name" in values and values["full_name"] is None:
        fail(422, "INVALID_PROFILE", "Full name cannot be empty.")
    for key, value in values.items():
        setattr(user, key, value)
    db.flush()
    return user
