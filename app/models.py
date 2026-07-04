# =============================================================================
# app/models.py – Pydantic response models
# =============================================================================
from typing import List
from pydantic import BaseModel


class CurrentWeather(BaseModel):
    city: str
    country: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    condition: str
    description: str
    wind_speed_ms: float
    visibility_m: int
    timestamp: str   # ISO-8601 UTC


class DailyForecast(BaseModel):
    date: str          # YYYY-MM-DD
    temp_min_c: float
    temp_max_c: float
    humidity_pct: int
    condition: str
    description: str


class ForecastResponse(BaseModel):
    city: str
    country: str
    days: int
    forecast: List[DailyForecast]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
