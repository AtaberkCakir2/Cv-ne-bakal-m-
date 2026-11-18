"""Cv'ne Bakalım! API giriş noktası.

Çalıştırma (backend/ klasöründe): uvicorn app.main:app --reload
OpenAPI dokümanı: http://127.0.0.1:8000/docs · Ayrıntılı rehber: docs/api/README.md
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import mount_admin
from app.api.routers import analyses, auth, catalog, health, users
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.openapi import install_openapi
from app.core.rate_limit import GeneralRateLimitMiddleware, Limit, MemoryCounterStore, RateLimiter, redis_lifespan
from app.core.uploads import UploadSizeLimitMiddleware, keep_uploads_in_memory
from app.db.session import get_sessionmaker
from app.services.analysis_queue import build_analysis_queue
from app.services.email import OutboxEmailSender

API_DESCRIPTION = """Cv'ne Bakalım! REST API. Sözleşme: `contracts/api.md` · Rehber ve örnek akış: `docs/api/README.md`.

- **Kimlik doğrulama:** `POST /auth/login` ile alınan access token `Authorization: Bearer <token>` başlığında gider.
  Süresi dolunca `POST /auth/refresh` ile yenilenir (refresh token her kullanımda değişir).
- **Hatalar:** Tüm 4xx/5xx yanıtları RFC 7807 biçimindedir (`application/problem+json`, şema: `Problem`).
- **İstek sınırları:** Genel 100/dk/IP; giriş, kayıt, e-posta doğrulama ve şifre sıfırlama 10/dk/IP;
  analiz 5/saat/kullanıcı. Sınır aşılınca 429 ve `Retry-After` başlığı döner.
- **Gizlilik:** CV dosyası saklanmaz; sadece SHA-256 özeti ve çıkarılan yetkinlikler tutulur.
"""

OPENAPI_TAGS = [
    {"name": "Sistem", "description": "Canlılık ve hazırlık kontrolleri (izleme ve yük dengeleyici için)."},
    {"name": "Kimlik doğrulama", "description": "Kayıt, giriş, token yenileme, e-posta doğrulama, şifre sıfırlama."},
    {"name": "Kullanıcı", "description": "Profil ve KVKK hakları: onaylar, verilerimi indir, hesabımı sil."},
    {"name": "Analiz", "description": "CV yükleme, analiz durumu ve sonucu, geçmiş, silme, geri bildirim."},
    {
        "name": "Katalog",
        "description": "Hedef pozisyonlar, en çok istenen yetkinlikler, eğitim kaynakları. Giriş gerekmez.",
    },
]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    keep_uploads_in_memory()

    # Redis istemcisi lifespan'de açılır (event loop'a bağlı); o zamana kadar sayaçlar bellekte.
    limiter = RateLimiter(MemoryCounterStore(), settings) if settings.rate_limit_enabled else None

    app = FastAPI(
        lifespan=redis_lifespan(limiter, settings.redis_url) if limiter else None,
        title=settings.app_name,
        version="0.1.0",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )
    register_exception_handlers(app)
    install_openapi(app)
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
    # Yönetim paneli /admin (T-063, Ataberk; app/admin/README.md).
    mount_admin(app, settings, get_sessionmaker())
    return app


app = create_app()
