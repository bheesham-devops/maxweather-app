# =============================================================================
# app/weather.py – OpenWeatherMap API client
# =============================================================================
from datetime import datetime, timezone
from typing import List

import httpx

from .config import get_settings
from .models import CurrentWeather, DailyForecast, ForecastResponse


class CityNotFoundError(Exception):
    """Raised when OpenWeatherMap returns 404 for the given city."""
    def __init__(self, city: str):
        self.city = city
        super().__init__(f"City not found: {city}")


class WeatherServiceError(Exception):
    """Raised on unexpected upstream errors."""


async def get_current_weather(city: str) -> CurrentWeather:
    """Fetch current weather conditions for a city from OpenWeatherMap."""
    settings = get_settings()
    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.openweather_base_url}/weather", params=params
            )
        except httpx.RequestError as exc:
            raise WeatherServiceError(
                f"Upstream request failed: {exc}"
            ) from exc

    if response.status_code == 404:
        raise CityNotFoundError(city)

    if response.status_code != 200:
        raise WeatherServiceError(
            f"OpenWeatherMap returned {response.status_code}: {response.text}"
        )

    data = response.json()
    ts = datetime.fromtimestamp(data["dt"], tz=timezone.utc).isoformat()

    return CurrentWeather(
        city=data["name"],
        country=data["sys"]["country"],
        temperature_c=round(data["main"]["temp"], 1),
        feels_like_c=round(data["main"]["feels_like"], 1),
        humidity_pct=data["main"]["humidity"],
        condition=data["weather"][0]["main"],
        description=data["weather"][0]["description"],
        wind_speed_ms=round(data["wind"].get("speed", 0.0), 1),
        visibility_m=data.get("visibility", 0),
        timestamp=ts,
    )


async def get_weather_forecast(city: str, days: int = 5) -> ForecastResponse:
    """Fetch up to 10-day forecast for a city. Free tier returns 3-hourly for 5 days."""
    if not 1 <= days <= 10:
        raise ValueError("days must be between 1 and 10")

    settings = get_settings()
    # Free tier: max 40 entries (5 days × 8 × 3-hourly intervals)
    cnt = min(days * 8, 40)
    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": "metric",
        "cnt": cnt,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.openweather_base_url}/forecast", params=params
            )
        except httpx.RequestError as exc:
            raise WeatherServiceError(
                f"Upstream request failed: {exc}"
            ) from exc

    if response.status_code == 404:
        raise CityNotFoundError(city)

    if response.status_code != 200:
        raise WeatherServiceError(
            f"OpenWeatherMap returned {response.status_code}: {response.text}"
        )

    data = response.json()

    # Aggregate 3-hourly entries into daily summaries
    daily: dict[str, list] = {}
    for item in data["list"]:
        date_str = datetime.fromtimestamp(
            item["dt"], tz=timezone.utc
        ).strftime("%Y-%m-%d")
        daily.setdefault(date_str, []).append(item)

    forecast: List[DailyForecast] = []
    for date_str, items in sorted(daily.items())[:days]:
        temps = [i["main"]["temp"] for i in items]
        humidities = [i["main"]["humidity"] for i in items]

        # Prefer the midday entry for the representative condition
        midday = [
            i for i in items
            if datetime.fromtimestamp(
                i["dt"], tz=timezone.utc
            ).strftime("%H:%M") == "12:00"
        ]
        rep = midday[0] if midday else items[len(items) // 2]

        forecast.append(
            DailyForecast(
                date=date_str,
                temp_min_c=round(min(temps), 1),
                temp_max_c=round(max(temps), 1),
                humidity_pct=round(sum(humidities) / len(humidities)),
                condition=rep["weather"][0]["main"],
                description=rep["weather"][0]["description"],
            )
        )

    return ForecastResponse(
        city=data["city"]["name"],
        country=data["city"]["country"],
        days=len(forecast),
        forecast=forecast,
    )
