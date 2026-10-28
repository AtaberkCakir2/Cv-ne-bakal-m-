"""Uygulama ayarları. Değerler ortam değişkenlerinden veya repo kökündeki .env dosyasından okunur."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

# Sadece local/test ortamında kullanılan sabit anahtar; başka ortamda kullanılırsa uygulama açılmaz.
DEV_JWT_SECRET = "careerai-local-dev-jwt-secret-do-not-use-in-prod"  # noqa: S105


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

    # Kimlik doğrulama (T-037). JWT_SECRET production'da mutlaka .env'den gelir (uzun, rastgele).
    jwt_secret: str = Field(default=DEV_JWT_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    # KVKK rızasındaki IP hash'inin anahtarı; production'da JWT_SECRET'tan ayrı verin (yoksa JWT_SECRET kullanılır).
    ip_hash_secret: str | None = Field(default=None, min_length=32)
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    verify_email_ttl_hours: int = 24
    reset_password_ttl_minutes: int = 60
    # E-postadaki doğrulama / sıfırlama bağlantılarının açılacağı web arayüzü adresi
    frontend_url: str = "http://127.0.0.1:5173"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_explicit_dev(self) -> bool:
        """ENVIRONMENT=local/test açıkça verilmiş mi? Varsayılan değer sayılmaz (unutulan ayar dev'e düşmesin)."""
        return "environment" in self.model_fields_set and self.environment in ("local", "test")

    @property
    def auth_ready(self) -> bool:
        """Token üretilebilir mi: gerçek JWT_SECRET verilmiş ya da açıkça local/test ortamı."""
        return self.jwt_secret != DEV_JWT_SECRET or self.is_explicit_dev

    @model_validator(mode="after")
    def _secret_must_be_set_outside_local(self) -> "Settings":
        if self.environment not in ("local", "test") and self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("JWT_SECRET ayarlanmamış: local/test dışında geliştirme anahtarı kullanılamaz.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
