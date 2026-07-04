# =============================================================================
# tests/conftest.py – Shared fixtures
# =============================================================================
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings, Settings


@pytest.fixture
def client():
    """Sync test client (used in non-async tests)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Inject a fake API key so Settings() never fails in tests."""
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-api-key-12345")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Canned OpenWeatherMap responses
# ---------------------------------------------------------------------------
CURRENT_OWM_RESPONSE = {
    "name": "Singapore",
    "sys": {"country": "SG"},
    "main": {"temp": 31.2, "feels_like": 35.1, "humidity": 82},
    "weather": [{"main": "Clouds", "description": "broken clouds"}],
    "wind": {"speed": 3.1},
    "visibility": 10000,
    "dt": 1751616000,  # 2026-07-04T08:00:00Z
}

FORECAST_OWM_RESPONSE = {
    "city": {"name": "Singapore", "country": "SG"},
    "list": [
        {
            "dt": 1751616000,  # 2026-07-04 08:00
            "main": {"temp": 29.0, "temp_min": 28.0, "temp_max": 31.0, "humidity": 85},
            "weather": [{"main": "Rain", "description": "moderate rain"}],
        },
        {
            "dt": 1751659200,  # 2026-07-04 20:00
            "main": {"temp": 27.0, "temp_min": 26.5, "temp_max": 30.0, "humidity": 88},
            "weather": [{"main": "Clouds", "description": "overcast clouds"}],
        },
        {
            "dt": 1751702400,  # 2026-07-05 08:00
            "main": {"temp": 30.0, "temp_min": 28.5, "temp_max": 32.0, "humidity": 80},
            "weather": [{"main": "Clear", "description": "clear sky"}],
        },
    ],
}
