"""Typed runtime settings shared by SQLAlchemy and Alembic."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings; values are safe defaults for local development."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://pokedex:pokedex@localhost:5432/pokedex",
        validation_alias="DATABASE_URL",
    )


settings = Settings()
