# =============================================================================
# tests/test_api.py – Unit tests for all API endpoints
# =============================================================================
import pytest
import respx
import httpx

from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import CURRENT_OWM_RESPONSE, FORECAST_OWM_RESPONSE


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------
def test_health_returns_200(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "timestamp" in body


# ---------------------------------------------------------------------------
# GET /current
# ---------------------------------------------------------------------------
@respx.mock
def test_current_weather_success(client: TestClient):
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(200, json=CURRENT_OWM_RESPONSE)
    )

    response = client.get("/current", params={"city": "Singapore"})

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Singapore"
    assert body["country"] == "SG"
    assert body["temperature_c"] == 31.2
    assert body["humidity_pct"] == 82
    assert body["condition"] == "Clouds"
    assert body["wind_speed_ms"] == 3.1
    assert "timestamp" in body


@respx.mock
def test_current_weather_city_not_found(client: TestClient):
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(404, json={"message": "city not found"})
    )

    response = client.get("/current", params={"city": "NotARealCity12345"})

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "CityNotFound"
    assert "NotARealCity12345" in body["detail"]


def test_current_weather_missing_city_param(client: TestClient):
    response = client.get("/current")
    assert response.status_code == 422  # FastAPI validation error


@respx.mock
def test_current_weather_upstream_error(client: TestClient):
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(500, json={"message": "internal error"})
    )

    response = client.get("/current", params={"city": "Singapore"})

    assert response.status_code == 502
    assert response.json()["error"] == "WeatherServiceUnavailable"


# ---------------------------------------------------------------------------
# GET /forecast
# ---------------------------------------------------------------------------
@respx.mock
def test_forecast_success(client: TestClient):
    respx.get("https://api.openweathermap.org/data/2.5/forecast").mock(
        return_value=httpx.Response(200, json=FORECAST_OWM_RESPONSE)
    )

    response = client.get("/forecast", params={"city": "Singapore", "days": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Singapore"
    assert body["country"] == "SG"
    assert len(body["forecast"]) == 2
    # First day should have rain as the representative condition (first entry)
    assert body["forecast"][0]["condition"] in ("Rain", "Clouds", "Clear")
    assert body["forecast"][0]["temp_min_c"] <= body["forecast"][0]["temp_max_c"]


@respx.mock
def test_forecast_city_not_found(client: TestClient):
    respx.get("https://api.openweathermap.org/data/2.5/forecast").mock(
        return_value=httpx.Response(404, json={"message": "city not found"})
    )

    response = client.get("/forecast", params={"city": "NotARealCity12345"})

    assert response.status_code == 404
    assert response.json()["error"] == "CityNotFound"


def test_forecast_days_out_of_range(client: TestClient):
    response = client.get("/forecast", params={"city": "Singapore", "days": 11})
    assert response.status_code == 422  # FastAPI ge/le validation


def test_forecast_days_zero(client: TestClient):
    response = client.get("/forecast", params={"city": "Singapore", "days": 0})
    assert response.status_code == 422


def test_forecast_missing_city_param(client: TestClient):
    response = client.get("/forecast")
    assert response.status_code == 422
