from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services import health as health_service

router = APIRouter(prefix="/health", tags=["Sistem"])


@router.get("", response_model=HealthResponse, summary="Canlılık")
async def health() -> HealthResponse:
    """Uygulama ayakta mı? Bağımlılıklara bakmaz; uptime izleme bunu kullanır."""
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Hazırlık (DB, Redis, Ollama)",
    responses={503: {"model": ReadinessResponse, "description": "En az bir bağımlılık erişilemez"}},
)
async def ready(settings: Annotated[Settings, Depends(get_settings)]) -> JSONResponse:
    """Bağımlılıklara erişilebiliyor mu? Erişilemeyen varsa 503 döner (deploy sonrası smoke test ve izleme)."""
    result = await health_service.readiness(settings)
    return JSONResponse(status_code=200 if result.status == "ready" else 503, content=result.model_dump())
