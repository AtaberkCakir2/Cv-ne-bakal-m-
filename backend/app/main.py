"""CareerAI API giriş noktası.

Çalıştırma (backend/ klasöründe): uvicorn app.main:app --reload
OpenAPI dokümanı: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import analyses, auth, catalog, health, users
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import GeneralRateLimitMiddleware, Limit, MemoryCounterStore, RateLimiter, redis_lifespan
from app.core.uploads import UploadSizeLimitMiddleware, keep_uploads_in_memory
from app.services.analysis_queue import build_analysis_queue
from app.services.email import OutboxEmailSender


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    keep_uploads_in_memory()

    # Redis istemcisi lifespan'de açılır (event loop'a bağlı); o zamana kadar sayaçlar bellekte.
    limiter = RateLimiter(MemoryCounterStore(), settings) if settings.rate_limit_enabled else None

    # Swagger arayüzü ve şema production'da kapalı (güvenlik raporu G-6); staging ve local'de açık.
    docs_enabled = not settings.is_production
    app = FastAPI(
        lifespan=redis_lifespan(limiter, settings.redis_url) if limiter else None,
        title=settings.app_name,
        version="0.1.0",
        description="CareerAI REST API. Sözleşme: contracts/api.md · Hatalar RFC 7807 (application/problem+json).",
        openapi_url=f"{settings.api_prefix}/openapi.json" if docs_enabled else None,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
    )
    register_exception_handlers(app)
    if limiter is not None:
        # CORS'tan önce eklenir, yani onun içinde çalışır: 429 yanıtı da CORS başlıklarını alır.
        app.state.rate_limiter = limiter
        app.add_middleware(
            GeneralRateLimitMiddleware,
            limiter=limiter,
            limit=Limit("general", settings.rate_limit_general_per_minute, 60),
            exempt_paths=frozenset({f"{settings.api_prefix}/health"}),
        )
    # Büyük yüklemeler gövde okunmadan reddedilir (bellek koruması). CORS'un içinde: 413/411 yanıtı da CORS
    # başlıklarını alır, tarayıcı bunu ağ hatası sanmaz (T-052).
    app.add_middleware(UploadSizeLimitMiddleware, paths=(f"{settings.api_prefix}/analyses",))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Retry-After: web, 429/503'te kalan süreyi gösterebilsin (T-052).
        expose_headers=["X-Request-ID", "Retry-After"],
    )
    # En dışta: istek kimliği her yanıta (hatalar dahil) eklenir.
    app.add_middleware(RequestContextMiddleware)

    app.state.analysis_queue = build_analysis_queue(settings)
    # GEÇİCİ: gerçek e-posta servisi seçilene kadar iletiler bellekte; bağlantı sadece local'de loglanır.
    app.state.email_sender = OutboxEmailSender(log_links=settings.is_explicit_dev and settings.environment == "local")

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(analyses.router, prefix=settings.api_prefix)
    app.include_router(catalog.roles_router, prefix=settings.api_prefix)
    app.include_router(catalog.skills_router, prefix=settings.api_prefix)
    return app


app = create_app()
