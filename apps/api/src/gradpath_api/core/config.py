"""Validated application settings loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with secure, explicit defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GRADPATH_",
        extra="ignore",
    )

    app_name: str = "GradPath AI API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    enable_api_docs: bool = True
    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://gradpath:gradpath_dev@localhost:5432/gradpath"
    )


@lru_cache
def get_settings() -> Settings:
    """Return one settings instance per process."""

    return Settings()
