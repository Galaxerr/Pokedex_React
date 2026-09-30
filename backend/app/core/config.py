"""Configuration placeholder for the future runtime settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Empty settings boundary; domain configuration is deferred."""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
