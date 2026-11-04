"""Uygulama ayarları. Değerler ortam değişkenlerinden veya repo kökündeki .env dosyasından okunur."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

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

    # "localhost" değil 127.0.0.1: Windows'ta localhost önce IPv6'ya (::1) çözülür, docker-compose portları
    # ise sadece 127.0.0.1'e açık. localhost ile her bağlantı ~2 sn bekleyip IPv4'e düşer, Redis zaman aşımına uğrar.
    database_url: str = "postgresql+psycopg://careerai:careerai@127.0.0.1:5432/careerai"
    redis_url: str = "redis://127.0.0.1:6379/0"
    ollama_url: str = "http://127.0.0.1:11434"

    # /health/ready içindeki her bağımlılık kontrolü için zaman aşımı (saniye)
    readiness_timeout_s: float = 2.0
    # Sadece kendi alan adlarımıza izin verilir (karar: güvenlik incelemesi, T-064)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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

    # İstek sınırları (T-050, app/core/rate_limit.py). Sayaçlar redis_url'deki Redis'te tutulur.
    rate_limit_enabled: bool = True
    rate_limit_general_per_minute: int = 100
    rate_limit_auth_per_minute: int = 10
    rate_limit_analyses_per_hour: int = 5

    # Analiz kuyruğu (T-039). CV baytları kalıcılığı KAPALI ayrı bir Redis'te durur (karar #9): REDIS_URL'den farklı.
    cv_redis_url: str | None = None
    analysis_timeout_s: int = 180
    analysis_cv_ttl_s: int = 3600
    # Bu süreyi geçip bitmeyen analiz askıda sayılır (işçi öldü, sert süre sınırı). CV TTL'inden uzun olmalı.
    analysis_stale_after_s: int = 3900
    # Bekleyen CV sayısı; her biri en fazla 5 MB. Tek işçi ve iş başına ~6 dk (180 sn x 2) ile hepsi TTL içinde biter.
    analysis_queue_limit: int = 8

    @property
    def cv_store_url(self) -> str | None:
        """CV deposunun adresi. Sadece local/test'te ayrı Redis olmadan çalışılır (orada yalnızca sahte CV var)."""
        if self.cv_redis_url:
            return self.cv_redis_url
        return urlsplit(self.redis_url)._replace(path="/1").geturl() if self.is_explicit_dev else None

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
        if self.environment not in ("local", "test") and self.cv_redis_url == self.redis_url:
            raise ValueError(
                "CV_REDIS_URL, REDIS_URL ile aynı olamaz: broker kalıcıdır, CV diske yazılırdı (karar #9)."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
