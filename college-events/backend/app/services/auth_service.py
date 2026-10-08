import hashlib
import secrets
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage
from urllib.parse import urlencode

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import utcnow
from app.errors import fail
from app.models import Role, User
from app.schemas.auth import Credentials, Signup
from app.security import dummy_password_hash, hash_password, verify_password


def signup(db: Session, data: Signup) -> User:
    settings = get_settings()
    existing = db.scalar(select(User.id).where(or_(User.email == str(data.email),
                      User.student_id == data.student_id if data.student_id else False)))
    if existing:
        fail(409, "ACCOUNT_EXISTS", "An account with these details already exists.")
    values = data.model_dump(exclude={"password", "role"})
    user_role = data.role if data.role else Role.STUDENT
    # Map frontend "organizer" (which might be passed as string if not strictly enum, but Pydantic parses it) to Role.MANAGER if needed
    if isinstance(user_role, str) and user_role.upper() == "ORGANIZER":
        user_role = Role.MANAGER
    user = User(**values, password_hash=hash_password(data.password.get_secret_value()), role=user_role)
    db.add(user)
    db.flush()
    return user


def login(db: Session, data: Credentials) -> User:
    user = db.scalar(select(User).where(User.email == str(data.email)))
    password_ok = verify_password(data.password.get_secret_value(),
                                  user.password_hash if user else dummy_password_hash())
    if not user or not password_ok or not user.is_active:
        fail(401, "INVALID_CREDENTIALS", "Invalid email or password.")
    return user


def set_password(user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    user.token_version += 1
    user.reset_token_hash = None
    user.reset_expires_at = None


def change_password(db: Session, user: User, current: str, new: str) -> None:
    user = db.scalar(select(User).where(User.id == user.id).with_for_update()
                     .execution_options(populate_existing=True))
    if not verify_password(current, user.password_hash):
        fail(400, "INVALID_CURRENT_PASSWORD", "Current password is incorrect.")
    set_password(user, new)
    db.flush()


def send_reset_email(email: str, token: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = "Reset your college events password"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    separator = "&" if "?" in settings.password_reset_url else "?"
    url = settings.password_reset_url + separator + urlencode({"token": token})
    message.set_content(f"Reset your password: {url}\nThis link expires in "
                        f"{settings.password_reset_expire_minutes} minutes. "
                        "Ignore this email if you did not request it.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value()
                       if settings.smtp_password else "")
        smtp.send_message(message)


def request_password_reset(db: Session, email: str) -> None:
    settings = get_settings()
    if not settings.reset_available:
        fail(503, "RESET_UNAVAILABLE", "Email password reset is not configured. Contact the college administrator.")
    user = db.scalar(select(User).where(User.email == email.strip().lower(), User.is_active.is_(True))
                     .with_for_update())
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token_hash = hashlib.sha256(token.encode()).hexdigest()
        user.reset_expires_at = utcnow() + timedelta(minutes=settings.password_reset_expire_minutes)
        db.flush()
        try:
            send_reset_email(user.email, token)
        except (OSError, smtplib.SMTPException):
            fail(503, "RESET_DELIVERY_FAILED", "Password reset delivery is temporarily unavailable.")


def reset_password(db: Session, token: str, password: str) -> None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    user = db.scalar(select(User).where(User.reset_token_hash == digest).with_for_update())
    if not user or not user.is_active or not user.reset_expires_at or user.reset_expires_at <= utcnow():
        fail(400, "INVALID_RESET_TOKEN", "Invalid or expired password reset token.")
    set_password(user, password)
    db.flush()
