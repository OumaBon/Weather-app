"""Application settings, read from environment variables and the .env file."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every setting the app needs, with its type and a safe default."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "kenya-weather"
    open_meteo_geocode_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    http_timeout_seconds: float = Field(default=10, gt=0, le=60)


@lru_cache
def get_settings() -> Settings:
    """Create the settings once, then reuse the same object everywhere."""
    return Settings()
