import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, DbSession
from app.api.rate_limits import AnalysesRateLimit
from app.core.errors import problem
from app.db.models import Analysis
from app.repositories.analyses import SqlAnalysisRepository
from app.schemas.analyses import (
    ERROR_MESSAGES,
    AnalysisCreated,
    AnalysisErrorOut,
    AnalysisModelOut,
    AnalysisOut,
    TargetRoleOut,
)
from app.services.analyses import AnalysisService, UnknownRole
from app.services.analysis_queue import QueueUnavailable
from app.services.cv_validation import CvRejected

router = APIRouter(prefix="/analyses", tags=["Analiz"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}
_RETRY_AFTER_S = 60


def get_analysis_service(request: Request, db: DbSession) -> AnalysisService:
    return AnalysisService(SqlAnalysisRepository(db), request.app.state.analysis_queue)


Analyses = Annotated[AnalysisService, Depends(get_analysis_service)]


def _out(analysis: Analysis) -> AnalysisOut:
    code = analysis.error_code
    return AnalysisOut(
        analysis_id=analysis.id,
        status=analysis.status,
        target_role=TargetRoleOut(slug=analysis.target_role.slug, name=analysis.target_role.name),
        postings_analyzed=analysis.postings_analyzed,
        match_score=float(analysis.match_score) if analysis.match_score is not None else None,
        model=(
            AnalysisModelOut(name=analysis.model_name, prompt_version=analysis.prompt_version)
            if analysis.model_name and analysis.prompt_version
            else None
        ),
        error=AnalysisErrorOut(code=code, message=ERROR_MESSAGES[code]) if code else None,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
    )


@router.post(
    "",
    status_code=202,
    response_model=AnalysisCreated,
    summary="CV yükle ve analiz başlat",
    dependencies=[AnalysesRateLimit],
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        411: {"description": "Content-Length yok", **_PROBLEM},
        413: {"description": "Dosya 5 MB'tan büyük (PDF_TOO_LARGE)", **_PROBLEM},
        415: {"description": "PDF değil (PDF_UNREADABLE)", **_PROBLEM},
        422: {
            "description": "Bozuk/şifreli PDF (PDF_UNREADABLE), 5 sayfadan uzun (PDF_TOO_LARGE) veya eksik alan",
            **_PROBLEM,
        },
        429: {"description": "Saatlik analiz sınırı", **_PROBLEM},
        503: {"description": "Kuyruk dolu veya kullanılamıyor", **_PROBLEM},
    },
)
def create_analysis(
    request: Request,
    file: Annotated[UploadFile, File(description="CV (PDF, en fazla 5 MB ve 5 sayfa)")],
    target_role_id: Annotated[int, Form(ge=1, description="Hedef pozisyon kimliği")],
    user: CurrentUser,
    service: Analyses,
) -> AnalysisCreated | JSONResponse:
    """CV dosyası diske yazılmaz ve saklanmaz; sadece SHA-256 özeti ve sayfa sayısı kaydedilir.
    Sonuç için `GET /analyses/{id}` yoklanır."""
    # Eş zamanlı def: FastAPI iş parçacığında çalıştırır, veritabanı ve Redis olay döngüsünü bekletmez.
    content = file.file.read()
    file.file.close()
    try:
        analysis_id = service.create(user.id, content, file.content_type, target_role_id)
    except CvRejected as exc:
        return problem(exc.status, exc.detail, request, code=exc.code)
    except UnknownRole:
        return problem(422, "Pozisyon bulunamadı.", request)
    except QueueUnavailable:
        response = problem(503, "Analiz şu anda başlatılamıyor. Lütfen biraz sonra tekrar deneyin.", request)
        response.headers["Retry-After"] = str(_RETRY_AFTER_S)
        return response
    finally:
        del content
    return AnalysisCreated(analysis_id=analysis_id, status="queued")


@router.get(
    "/{analysis_id}",
    response_model=AnalysisOut,
    summary="Analiz durumu ve sonucu",
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        404: {"description": "Analiz bulunamadı", **_PROBLEM},
    },
)
def get_analysis(analysis_id: uuid.UUID, user: CurrentUser, service: Analyses, response: Response) -> AnalysisOut:
    """Durum: queued, processing, done, failed. Başkasının analizi de 404 döner. (Liste, silme: T-048.)"""
    response.headers["Cache-Control"] = "no-store"
    analysis = service.get(analysis_id, user.id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    return _out(analysis)
