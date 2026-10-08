from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import get_settings
from app.database import utcnow
from app.schemas.auth import Signup


def test_public_signup_rejects_roles_and_normalizes_email():
    payload = {"full_name": "Student One", "email": "Person@College.edu", "password": "long-password-123"}
    assert Signup(**payload).email == "person@college.edu"
    with pytest.raises(ValidationError):
        Signup(**payload, role="MANAGER")


def test_access_tokens_reject_wrong_purpose_and_expiration():
    from app.security import decode_access_token

    settings = get_settings()
    claims = {"sub": str(uuid4()), "ver": 0, "type": "access", "aud": "college-events-api",
              "iss": settings.app_name, "iat": utcnow(), "exp": utcnow() - timedelta(seconds=1)}
    expired = jwt.encode(claims, settings.jwt_secret_key.get_secret_value(), algorithm="HS256")
    with pytest.raises(HTTPException) as error:
        decode_access_token(expired)
    assert error.value.status_code == 401
    claims["exp"] = utcnow() + timedelta(minutes=1)
    claims["type"] = "ticket"
    wrong = jwt.encode(claims, settings.jwt_secret_key.get_secret_value(), algorithm="HS256")
    with pytest.raises(HTTPException):
        decode_access_token(wrong)


def test_auth_rate_limit_is_enforced():
    from app.security import AuthRateLimiter

    limiter = AuthRateLimiter(limit=2, window_seconds=60)
    limiter.check("192.0.2.1")
    limiter.check("192.0.2.1")
    with pytest.raises(HTTPException) as error:
        limiter.check("192.0.2.1")
    assert error.value.status_code == 429
    limiter.check("192.0.2.2")
