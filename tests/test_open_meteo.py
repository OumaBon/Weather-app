"""Tests for the CLIENT layer. No real network: every response is faked."""

import httpx
import pytest

from app.config import Settings
from app.exceptions import CityNotFoundError, WeatherServiceUnavailableError
from app.services.open_meteo import OpenMeteoClient

KISUMU = {"results": [{"name": "Kisumu", "country": "Kenya", "latitude": -0.1, "longitude": 34.75}]}
CURRENT = {"current": {"temperature_2m": 27.4, "relative_humidity_2m": 61,
                       "wind_speed_10m": 12.3, "weather_code": 2}}


def make_client(handler) -> OpenMeteoClient:
    """Build a client whose 'internet' is the handler function we pass in."""
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenMeteoClient(http, Settings())


# ---------- find_city ----------

async def test_find_city_returns_location():
    client = make_client(lambda request: httpx.Response(200, json=KISUMU))
    location = await client.find_city("Kisumu")
    assert location.name == "Kisumu"
    assert location.latitude == -0.1


async def test_find_city_sends_the_city_name():
    seen = {}

    def handler(request):
        seen["name"] = request.url.params["name"]
        return httpx.Response(200, json=KISUMU)

    await make_client(handler).find_city("Kisumu")
    assert seen["name"] == "Kisumu"


async def test_unknown_city_raises_city_not_found():
    client = make_client(lambda request: httpx.Response(200, json={}))
    with pytest.raises(CityNotFoundError):
        await client.find_city("Atlantis")


# ---------- get_current_conditions ----------

async def test_current_conditions_are_parsed():
    client = make_client(lambda request: httpx.Response(200, json=CURRENT))
    now = await client.get_current_conditions(-0.1, 34.75)
    assert now.temperature_2m == 27.4
    assert now.weather_code == 2


# ---------- failures: every one becomes WeatherServiceUnavailableError ----------

def raise_timeout(request):
    raise httpx.ReadTimeout("too slow")


def raise_no_network(request):
    raise httpx.ConnectError("no network")


@pytest.mark.parametrize(
    "handler",
    [
        raise_timeout,                                                 # too slow
        raise_no_network,                                              # no internet
        lambda request: httpx.Response(500),                           # server error
        lambda request: httpx.Response(200, text="<html>oops</html>"), # not JSON
        lambda request: httpx.Response(200, json={"current": {"temperature_2m": "hot"}}),  # wrong shape
    ],
    ids=["timeout", "no-network", "http-500", "not-json", "bad-shape"],
)
async def test_failures_become_service_unavailable(handler):
    client = make_client(handler)
    with pytest.raises(WeatherServiceUnavailableError):
        await client.get_current_conditions(-0.1, 34.75)