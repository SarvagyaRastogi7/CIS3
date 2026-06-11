from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cashflow Forecasting API"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False

    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
        ]
    )

    max_upload_bytes: int = 5 * 1024 * 1024
    min_history_months: int = 12
    arima_max_p: int = 2
    arima_max_d: int = 1
    arima_max_q: int = 2

    log_level: str = "INFO"

    llm_enabled: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 120
    openai_base_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
