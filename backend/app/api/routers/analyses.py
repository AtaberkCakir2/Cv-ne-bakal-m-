import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.errors import problem
from app.schemas.analyses import AnalysisCreated
from app.services.analyses import AnalysisService
from app.services.cv_validation import CvRejected

router = APIRouter(prefix="/analyses", tags=["Analiz"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}


def get_analysis_service(request: Request) -> AnalysisService:
    service: AnalysisService = request.app.state.analysis_service
    return service


# TODO(T-037): kimlik doğrulama; analiz kullanıcıya bağlanacak ve sadece sahibi görebilecek.
# TODO(T-050): saatte 5 analiz sınırı.


@router.post(
    "",
    status_code=202,
    response_model=AnalysisCreated,
    summary="CV yükle ve analiz başlat",
    responses={
        411: {"description": "Content-Length yok", **_PROBLEM},
        413: {"description": "Dosya 5 MB'tan büyük (PDF_TOO_LARGE)", **_PROBLEM},
        415: {"description": "PDF değil (NOT_PDF)", **_PROBLEM},
        422: {"description": "Bozuk/şifreli PDF, 5 sayfadan uzun veya eksik alan", **_PROBLEM},
    },
)
async def create_analysis(
    request: Request,
    file: Annotated[UploadFile, File(description="CV (PDF, en fazla 5 MB ve 5 sayfa)")],
    target_role_id: Annotated[int, Form(ge=1, description="Hedef pozisyon kimliği")],
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisCreated | JSONResponse:
    """CV dosyası diske yazılmaz ve saklanmaz; sadece SHA-256 özeti ve sayfa sayısı kaydedilir."""
    content = await file.read()
    await file.close()
    try:
        record = service.create(content, file.content_type, target_role_id)
    except CvRejected as exc:
        return problem(exc.status, exc.detail, request, code=exc.code)
    finally:
        del content
    return AnalysisCreated(analysis_id=record.id, status="queued")


@router.get(
    "/{analysis_id}",
    summary="Analiz sonucu",
    responses={404: {"description": "Analiz bulunamadı", **_PROBLEM}},
)
async def get_analysis(
    analysis_id: uuid.UUID, service: Annotated[AnalysisService, Depends(get_analysis_service)]
) -> dict[str, Any]:
    """Sonuç formatı: contracts/analysis_result.schema.json. (Liste, silme ve geri bildirim: T-048.)"""
    record = service.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    if record.result is not None:
        return record.result
    return {"analysis_id": str(record.id), "status": record.status, "created_at": record.created_at.isoformat()}
