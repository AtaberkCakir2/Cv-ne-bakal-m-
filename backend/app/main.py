"""CareerAI API giriş noktası.

Çalıştırma (backend/ klasöründe): uvicorn app.main:app --reload
OpenAPI dokümanı: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import health
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="CareerAI REST API. Sözleşme: contracts/api.md · Hatalar RFC 7807 (application/problem+json).",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    # En dışta: istek kimliği her yanıta (hatalar dahil) eklenir.
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router, prefix=settings.api_prefix)
    return app


app = create_app()
