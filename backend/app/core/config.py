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

    # "localhost" değil 127.0.0.1: Windows'ta localhost önce IPv6'ya (::1) çözülür, docker-compose portları
    # ise sadece 127.0.0.1'e açık. localhost ile her bağlantı ~2 sn bekleyip IPv4'e düşer, Redis zaman aşımına uğrar.
    database_url: str = "postgresql+psycopg://careerai:careerai@127.0.0.1:5432/careerai"
    redis_url: str = "redis://127.0.0.1:6379/0"
    ollama_url: str = "http://127.0.0.1:11434"

    # /health/ready içindeki her bağımlılık kontrolü için zaman aşımı (saniye)
    readiness_timeout_s: float = 2.0
    # Sadece kendi alan adlarımıza izin verilir (karar: güvenlik incelemesi, T-064)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
