"""Errors the application can raise. Every layer imports them from here."""


class WeatherError(Exception):
    """Base class for all weather-related errors."""


class CityNotFoundError(WeatherError):
    """The city name did not match any known place."""


class WeatherServiceUnavailableError(WeatherError):
    """Open-Meteo could not be reached, was too slow, or sent bad data."""