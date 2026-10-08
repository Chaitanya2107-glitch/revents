from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.errors import fail
from app.models import Role, User
from app.security import AuthRateLimiter, decode_access_token

Db = Annotated[Session, Depends(get_db, scope="function")]
bearer = HTTPBearer(auto_error=False)


def bearer_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if credentials is None:
        fail(401, "AUTH_REQUIRED", "Authentication required.")
    return credentials.credentials


def current_user(token: Annotated[str, Depends(bearer_token)], db: Db) -> User:
    claims = decode_access_token(token)
    user = db.get(User, UUID(claims["sub"]))
    if not user or not user.is_active or user.token_version != claims["ver"]:
        fail(401, "INVALID_TOKEN", "Invalid or expired authentication token.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def student_user(user: CurrentUser) -> User:
    if user.role != Role.STUDENT:
        fail(403, "STUDENT_REQUIRED", "A student account is required.")
    return user


def manager_user(user: CurrentUser) -> User:
    if user.role != Role.MANAGER:
        fail(403, "MANAGER_REQUIRED", "An event manager account is required.")
    return user


Student = Annotated[User, Depends(student_user)]
Manager = Annotated[User, Depends(manager_user)]
settings = get_settings()
auth_limiter = AuthRateLimiter(settings.auth_rate_limit_requests,
                              settings.auth_rate_limit_window_seconds)


def limit_auth(request: Request) -> None:
    auth_limiter.check(request.client.host if request.client else "unknown")
