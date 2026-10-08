from fastapi import APIRouter, Depends

from app.dependencies import CurrentUser, Db, limit_auth
from app.schemas.auth import ChangePassword, Credentials, LoginResponse, ResetPassword, ResetRequest, Signup
from app.schemas.common import Message
from app.schemas.user import UserOut
from app.security import create_access_token
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserOut, status_code=201, dependencies=[Depends(limit_auth)])
def register(data: Signup, db: Db):
    return auth_service.signup(db, data)


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(limit_auth)])
def login(data: Credentials, db: Db):
    user = auth_service.login(db, data)
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user, "role": user.role}


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/change-password", response_model=Message)
def change_password(data: ChangePassword, user: CurrentUser, db: Db):
    auth_service.change_password(db, user, data.current_password.get_secret_value(),
                                 data.new_password.get_secret_value())
    return {"message": "Password changed. Sign in again."}


@router.post("/password-reset/request", response_model=Message, dependencies=[Depends(limit_auth)])
def request_reset(data: ResetRequest, db: Db):
    auth_service.request_password_reset(db, str(data.email))
    return {"message": "If this account is eligible, password reset instructions have been sent."}


@router.post("/password-reset/confirm", response_model=Message, dependencies=[Depends(limit_auth)])
def confirm_reset(data: ResetPassword, db: Db):
    auth_service.reset_password(db, data.token, data.new_password.get_secret_value())
    return {"message": "Password reset. Sign in again."}
