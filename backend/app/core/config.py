"""Uygulama ayarları. Değerler ortam değişkenlerinden veya repo kökündeki .env dosyasından okunur."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CareerAI API"
    environment: str = Field(default="local", description="local | staging | production")
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://careerai:careerai@localhost:5432/careerai"
    redis_url: str = "redis://localhost:6379/0"
    ollama_url: str = "http://localhost:11434"

    # /health/ready içindeki her bağımlılık kontrolü için zaman aşımı (saniye)
    readiness_timeout_s: float = 2.0
    # Sadece kendi alan adlarımıza izin verilir (karar: güvenlik incelemesi, T-064)
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
