from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False, hide_input_in_errors=True
    )

    app_name: str = "College Event Management API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: SecretStr
    jwt_secret_key: SecretStr
    ticket_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    frontend_origin: str = "http://localhost:5173"
    cors_origins: str = ""
    public_base_url: str = "http://localhost:8000"
    allowed_college_email_domains: str = "college.edu"
    cancellation_cutoff_hours: int = Field(default=2, ge=0, le=720)
    checkin_before_minutes: int = Field(default=60, ge=0, le=1440)
    checkin_after_minutes: int = Field(default=60, ge=0, le=1440)
    ticket_presentation_ttl_minutes: int = Field(default=1440, ge=1, le=10080)
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = Field(default=5, ge=1, le=20)
    max_image_pixels: int = Field(default=20_000_000, ge=1, le=40_000_000)
    auth_rate_limit_requests: int = Field(default=20, ge=1, le=1000)
    auth_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True
    password_reset_url: str = "http://localhost:5173/reset-password"
    password_reset_expire_minutes: int = Field(default=30, ge=1, le=60)

    @property
    def origins(self) -> list[str]:
        return list(dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in (self.cors_origins or self.frontend_origin).split(",")
            if origin.strip()
        ))

    @property
    def college_domains(self) -> set[str]:
        return {domain.strip().lower() for domain in self.allowed_college_email_domains.split(",")
                if domain.strip()}

    @property
    def reset_available(self) -> bool:
        return bool(self.smtp_host and self.smtp_from_email)

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        for secret in (self.jwt_secret_key, self.ticket_secret_key):
            value = secret.get_secret_value()
            if len(value) < 32 or "REPLACE" in value.upper():
                raise ValueError("JWT and ticket secrets must be independent random values of 32+ characters")
        if self.jwt_secret_key == self.ticket_secret_key:
            raise ValueError("JWT_SECRET_KEY and TICKET_SECRET_KEY must differ")
        if not self.college_domains or any("@" in d or "." not in d for d in self.college_domains):
            raise ValueError("Configure at least one valid college email domain")
        for url in [*self.origins, self.public_base_url, self.password_reset_url]:
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
                raise ValueError("Configure explicit HTTP(S) URLs; wildcard origins are forbidden")
            if self.environment == "production" and parsed.scheme != "https":
                raise ValueError("Production public/frontend URLs must use HTTPS")
        if self.environment == "production" and self.smtp_host and not self.smtp_starttls:
            raise ValueError("Production SMTP requires STARTTLS")
        return self


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings(_env_file=None if os.environ.get("ENVIRONMENT") == "test" else ".env")
