"""CLIENT layer: the only code in the project that talks to Open-Meteo."""

import logging

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.exceptions import CityNotFoundError, WeatherServiceUnavailableError
from app.schemas.open_meteo import CurrentConditions, Location

log = logging.getLogger(__name__)


class OpenMeteoClient:
    """Fetches locations and current weather from Open-Meteo."""

    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http = http_client
        self._settings = settings

    async def find_city(self, city: str) -> Location:
        """Turn a city name into a Location. Raises CityNotFoundError if unknown."""
        data = await self._get_json(
            self._settings.open_meteo_geocode_url,
            {"name": city, "count": 1},
        )
        results = data.get("results") or []
        if not results:
            raise CityNotFoundError(f"City '{city}' not found")
        return self._parse(Location, results[0])

    async def get_current_conditions(self, latitude: float, longitude: float) -> CurrentConditions:
        """Get the current weather at a point on the map."""
        data = await self._get_json(
            self._settings.open_meteo_forecast_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
        )
        return self._parse(CurrentConditions, data.get("current"))

    # ----- private helpers: used only inside this class -----

    async def _get_json(self, url: str, params: dict) -> dict:
        """GET a URL and return its JSON. Every network failure becomes ONE error type."""
        try:
            response = await self._http.get(
                url, params=params, timeout=self._settings.http_timeout_seconds
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as error:
            log.error("Open-Meteo timed out: %s", error)
            raise WeatherServiceUnavailableError("Weather service timed out") from error
        except httpx.HTTPStatusError as error:
            log.error("Open-Meteo returned HTTP %s", error.response.status_code)
            raise WeatherServiceUnavailableError("Weather service returned an error") from error
        except httpx.RequestError as error:
            log.error("Could not reach Open-Meteo: %s", error)
            raise WeatherServiceUnavailableError("Weather service unreachable") from error
        except ValueError as error:  # response body was not valid JSON
            log.error("Open-Meteo sent invalid JSON: %s", error)
            raise WeatherServiceUnavailableError("Weather service sent bad data") from error

    @staticmethod
    def _parse(model, raw):
        """Validate raw data against a schema. Bad data becomes a clear error."""
        try:
            return model.model_validate(raw)
        except ValidationError as error:
            log.error("Unexpected data from Open-Meteo: %s", error)
            raise WeatherServiceUnavailableError("Weather service sent bad data") from error