from __future__ import annotations

from datetime import timedelta
from typing import List

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl: int = 900  # seconds (15m)
    refresh_token_ttl: int = 2592000  # seconds (30d)

    @property
    def access_timedelta(self) -> timedelta:
        return timedelta(seconds=self.access_token_ttl)

    @property
    def refresh_timedelta(self) -> timedelta:
        return timedelta(seconds=self.refresh_token_ttl)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=None, extra="ignore")

    # Core
    environment: str = "development"
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database/Cache
    database_url: str | None = None
    redis_url: str | None = None

    # Observability
    otel_enabled: bool = False

    # Security
    jwt_secret: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_ttl: int = 900
    refresh_token_ttl: int = 2592000

    # Rate limiting (tokens per minute)
    rate_limit_auth_per_minute: int = 30
    rate_limit_upload_per_minute: int = 10

    # Recon config
    recon_config_path: str | None = None

    @property
    def allow_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def security(self) -> SecuritySettings:
        return SecuritySettings(
            jwt_secret=self.jwt_secret,
            jwt_algorithm=self.jwt_algorithm,
            access_token_ttl=self.access_token_ttl,
            refresh_token_ttl=self.refresh_token_ttl,
        )


settings = AppSettings()  # type: ignore[call-arg]


