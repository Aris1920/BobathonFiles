from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/careerplanner"

    # JWT
    secret_key: str = "changeme-replace-with-a-random-64-char-hex-string"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # External API keys
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    handshake_api_key: str = ""
    indeed_publisher_id: str = ""
    usajobs_api_key: str = ""
    bls_api_key: str = ""


settings = Settings()
