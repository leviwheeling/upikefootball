from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "UPIKE Football Intelligence API"
    environment: str = "development"
    site_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("password", "PASSWORD", "SITE_PASSWORD"),
    )
    database_url: str = "postgresql+psycopg://upike:change-me@postgres:5432/upike_intel"
    redis_url: str = "redis://redis:6379/0"
    api_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    scraper_user_agent: str = (
        "UPIKEFootballIntel/0.1 (research; contact: your-email@example.com)"
    )
    scraper_min_delay_seconds: float = 10.0
    scraper_timeout_seconds: float = 30.0
    raw_document_root: Path = Path("data/raw")

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
