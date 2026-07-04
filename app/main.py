# =============================================================================
# app/main.py – FastAPI entry point
# =============================================================================
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

from .config import get_settings
from .models import CurrentWeather, ForecastResponse, HealthResponse, ErrorResponse
from .weather import (
    get_current_weather,
    get_weather_forecast,
    CityNotFoundError,
    WeatherServiceError,
)

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
_settings = get_settings()

logger = logging.getLogger("maxweather")
handler = logging.StreamHandler()
handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
)
logger.addHandler(handler)
logger.setLevel(getattr(logging, _settings.log_level.upper(), logging.INFO))
logger.propagate = False

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MaxWeather API",
    description=(
        "Real-time weather data and forecasts powered by OpenWeatherMap. "
        "All endpoints require a valid Entra ID Bearer token with the "
        "**Weather.Read** role (enforced by the APIM gateway)."
    ),
    version=_settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(CityNotFoundError)
async def city_not_found_handler(request, exc: CityNotFoundError):
    logger.warning("city_not_found", extra={"city": exc.city})
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="CityNotFound",
            detail=f"No weather data found for city: '{exc.city}'. "
                   "Check spelling or use a more specific name (e.g. 'London,GB').",
        ).model_dump(),
    )


@app.exception_handler(WeatherServiceError)
async def weather_service_error_handler(request, exc: WeatherServiceError):
    logger.error("upstream_error", extra={"detail": str(exc)})
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(
            error="WeatherServiceUnavailable",
            detail="The upstream weather provider is temporarily unavailable. "
                   "Please retry in a few seconds.",
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / readiness probe",
    tags=["ops"],
)
async def health():
    """Returns 200 OK — used by Kubernetes liveness and readiness probes."""
    return HealthResponse(
        status="ok",
        version=_settings.app_version,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


@app.get(
    "/current",
    response_model=CurrentWeather,
    summary="Get current weather",
    tags=["weather"],
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        502: {"model": ErrorResponse, "description": "Upstream service error"},
    },
)
async def current_weather(
    city: str = Query(
        ...,
        description="City name. Use 'City,CountryCode' for precision (e.g. 'Singapore,SG').",
        min_length=2,
        max_length=100,
    )
):
    """
    Returns current weather conditions for the given city.

    **Authentication:** Bearer token with `Weather.Read` role (validated by APIM).
    """
    logger.info("current_weather_request", extra={"city": city})
    result = await get_current_weather(city)
    logger.info("current_weather_response", extra={"city": result.city, "country": result.country})
    return result


@app.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get weather forecast",
    tags=["weather"],
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        422: {"description": "Validation error – days must be 1–10"},
        502: {"model": ErrorResponse, "description": "Upstream service error"},
    },
)
async def weather_forecast(
    city: str = Query(
        ...,
        description="City name. Use 'City,CountryCode' for precision (e.g. 'Singapore,SG').",
        min_length=2,
        max_length=100,
    ),
    days: int = Query(
        default=5,
        ge=1,
        le=10,
        description="Number of forecast days (1–10, default 5). Free tier is capped at 5 days.",
    ),
):
    """
    Returns daily weather forecast for up to 10 days.

    **Note:** The free OpenWeatherMap tier provides 3-hourly data for 5 days;
    requesting more than 5 days returns the same 5-day window.

    **Authentication:** Bearer token with `Weather.Read` role (validated by APIM).
    """
    logger.info("forecast_request", extra={"city": city, "days": days})
    result = await get_weather_forecast(city, days)
    logger.info("forecast_response", extra={"city": result.city, "days": result.days})
    return result
