from collections import OrderedDict, deque
from datetime import timedelta
from functools import lru_cache
from threading import Lock
from time import monotonic
from uuid import UUID

import jwt
from fastapi import HTTPException

from app.config import get_settings
from app.database import utcnow
from app.errors import fail
from app.models.user import User


@lru_cache
def password_hasher():
    from pwdlib import PasswordHash

    return PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher().hash(password)


@lru_cache
def dummy_password_hash() -> str:
    return hash_password("timing-only-dummy-password-never-used-for-an-account")


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hasher().verify(password, stored_hash)


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = utcnow()
    return jwt.encode({"sub": str(user.id), "ver": user.token_version, "type": "access",
                       "iat": now, "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
                       "aud": "college-events-api", "iss": settings.app_name},
                      settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret_key.get_secret_value(),
                            algorithms=[settings.jwt_algorithm], audience="college-events-api",
                            issuer=settings.app_name,
                            options={"require": ["sub", "ver", "type", "iat", "exp", "aud", "iss"]})
        UUID(claims["sub"])
        if claims["type"] != "access" or type(claims["ver"]) is not int:
            raise ValueError("Wrong token purpose")
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        fail(401, "INVALID_TOKEN", "Invalid or expired authentication token.")


class AuthRateLimiter:
    # ponytail: per-process limiter; use gateway limits across workers in production.
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.entries: OrderedDict[str, deque[float]] = OrderedDict()
        self.lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        with self.lock:
            for old_key in list(self.entries):
                if self.entries[old_key][-1] <= now - self.window_seconds:
                    del self.entries[old_key]
                else:
                    break
            if key not in self.entries and len(self.entries) >= 10000:
                raise HTTPException(429, {"code": "RATE_LIMITED", "message": "Try again later."},
                                    headers={"Retry-After": str(self.window_seconds)})
            attempts = self.entries.setdefault(key, deque())
            while attempts and attempts[0] <= now - self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.limit:
                raise HTTPException(429, {"code": "RATE_LIMITED", "message": "Too many attempts. Try again later."},
                                    headers={"Retry-After": str(self.window_seconds)})
            attempts.append(now)
            self.entries.move_to_end(key)
