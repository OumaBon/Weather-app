"""Shapes of the data we receive FROM Open-Meteo (not what we send out)."""

from pydantic import BaseModel


class Location(BaseModel):
    """One result from the geocoding service."""

    name: str
    country: str = ""
    latitude: float
    longitude: float


class CurrentConditions(BaseModel):
    """The 'current' block from the forecast service."""

    temperature_2m: float
    relative_humidity_2m: float
    wind_speed_10m: float
    weather_code: int