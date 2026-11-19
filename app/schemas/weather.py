"""Data shapes for weather results and errors."""

from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    """Current weather for one city, as returned by the API and MCP tool."""

    city: str = Field(examples=["Kisumu"])
    country: str = Field(examples=["Kenya"])
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    condition: str = Field(examples=["Partly cloudy"])
    temperature_c: float = Field(description="Air temperature at 2 m, in °C")
    humidity_percent: float = Field(ge=0, le=100)
    wind_speed_kmh: float = Field(ge=0)


class ErrorResponse(BaseModel):
    """The shape of every error the API returns."""

    detail: str = Field(examples=["City 'Atlantis' not found"])
