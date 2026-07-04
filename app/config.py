# =============================================================================
# app/config.py – Application settings loaded from environment variables
# =============================================================================
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Required – inject via K8s Secret
    openweather_api_key: str = "placeholder"

    # Optional – overrideable via ConfigMap
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    log_level: str = "INFO"
    app_name: str = "maxweather-api"
    app_version: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
