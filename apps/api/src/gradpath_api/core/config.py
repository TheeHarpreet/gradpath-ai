"""Validated application settings loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with secure, explicit defaults."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        env_prefix="GRADPATH_",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "GradPath AI API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    enable_api_docs: bool = True
    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://gradpath:gradpath_dev@localhost:5432/gradpath"
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    openai_model: str = "gpt-5.6-sol"
    openai_reasoning_effort: Literal[
        "none",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    ] = "medium"
    openai_store_responses: bool = False
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, gt=0, le=2000)
    embedding_batch_size: int = Field(default=32, gt=0, le=256)
    retrieval_limit: int = Field(default=3, gt=0, le=20)
    retrieval_candidate_limit: int = Field(default=8, gt=0, le=100)
    retrieval_rrf_k: int = Field(default=60, gt=0, le=1000)


@lru_cache
def get_settings() -> Settings:
    """Return one settings instance per process."""

    return Settings()
