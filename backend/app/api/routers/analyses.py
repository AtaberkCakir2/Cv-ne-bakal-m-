import uuid
from collections import defaultdict
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.api.rate_limits import AnalysesRateLimit
from app.core.errors import problem
from app.db.enums import SkillKind
from app.db.models import Analysis, AnalysisRecommendation, Resource
from app.repositories.analyses import SqlAnalysisRepository
from app.repositories.catalog import is_web_url
from app.schemas.analyses import (
    ERROR_MESSAGES,
    AnalysisCreated,
    AnalysisErrorOut,
    AnalysisListOut,
    AnalysisModelOut,
    AnalysisOut,
    AnalysisSummaryOut,
    FeedbackIn,
    FeedbackOut,
    MissingSkillOut,
    PresentSkillOut,
    ResourceOut,
    TargetRoleOut,
)
from app.services.analyses import AnalysisNotFinished, AnalysisService, ConsentWithdrawn, ResultCatalog, UnknownRole
from app.services.analysis_queue import QueueUnavailable
from app.services.cv_validation import CvRejected

router = APIRouter(prefix="/analyses", tags=["Analiz"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}
_RETRY_AFTER_S = 60


def get_analysis_service(request: Request, db: DbSession) -> AnalysisService:
    return AnalysisService(SqlAnalysisRepository(db), request.app.state.analysis_queue)


Analyses = Annotated[AnalysisService, Depends(get_analysis_service)]


def _error(analysis: Analysis) -> AnalysisErrorOut | None:
    code = analysis.error_code
    return AnalysisErrorOut(code=code, message=ERROR_MESSAGES[code]) if code else None


def _role(analysis: Analysis) -> TargetRoleOut:
    return TargetRoleOut(slug=analysis.target_role.slug, name=analysis.target_role.name)


def _resource(rec: AnalysisRecommendation, resource: Resource) -> ResourceOut:
    # Sözleşmede isteğe bağlı alanlar null olamaz: değer yoksa yanıtta da yok (response_model_exclude_unset).
    optional: dict[str, Any] = {"language": resource.language}
    if resource.duration_min is not None:
        optional["duration_min"] = resource.duration_min
    if rec.reason_text:
        optional["reason"] = rec.reason_text
    return ResourceOut(
        resource_id=resource.id,
        title=resource.title,
        url=resource.url,
        provider=resource.provider,
        level=resource.level,
        is_free=resource.is_free,
        **optional,
    )


def _skills(analysis: Analysis, catalog: ResultCatalog) -> tuple[list[PresentSkillOut], list[MissingSkillOut]]:
    names = catalog.skill_names
    present = [
        PresentSkillOut(skill=names[s.skill_id], level=s.level, confidence=float(s.confidence or 0), verified=True)
        for s in analysis.skills
        if s.kind == SkillKind.PRESENT
    ]
    present += [
        PresentSkillOut(skill=u.name, level=u.level, confidence=float(u.confidence or 0), verified=False)
        for u in analysis.unverified_skills
    ]
    present.sort(key=lambda p: (-p.confidence, p.skill))

    resources: dict[int, list[ResourceOut]] = defaultdict(list)
    for rec in analysis.recommendations:  # rank sırasıyla yüklenir (Analysis.recommendations order_by)
        resource = catalog.resources[rec.resource_id]
        # Link kontrolünden düşen kaynak katalogda olduğu gibi sonuçta da gösterilmez; http(s) dışı adres
        # (ör. hatalı veriyle gelen javascript:) hiç verilmez.
        if resource.is_alive and is_web_url(resource.url):
            resources[rec.skill_id].append(_resource(rec, resource))
    # Önce AI'ın verdiği öncelik, yoksa talep oranı. Yanıttaki öncelik sıra numarasıdır: 1, 2, 3… (sözleşme: ≥ 1,
    # önem sırası). AI'ın değerinde boşluk, tekrar veya boş değer olsa da numara sırayla çelişmez.
    missing_rows = sorted(
        (s for s in analysis.skills if s.kind == SkillKind.MISSING),
        key=lambda s: (s.priority is None, s.priority or 0, -(s.demand_ratio or 0), names[s.skill_id]),
    )
    missing = [
        MissingSkillOut(
            skill=names[s.skill_id],
            demand_ratio=float(s.demand_ratio or 0),
            priority=position,
            resources=resources.get(s.skill_id, []),
        )
        for position, s in enumerate(missing_rows, start=1)
    ]
    return present, missing


def _out(analysis: Analysis, catalog: ResultCatalog) -> AnalysisOut:
    # Sözleşmede bu üç alan null olamaz: değer yoksa yanıtta da yok (response_model_exclude_unset).
    optional: dict[str, Any] = {}
    if analysis.postings_analyzed is not None:
        optional["postings_analyzed"] = analysis.postings_analyzed
    if analysis.match_score is not None:
        optional["match_score"] = float(analysis.match_score)
    if analysis.model_name and analysis.prompt_version:
        optional["model"] = AnalysisModelOut(name=analysis.model_name, prompt_version=analysis.prompt_version)
    if analysis.feedback is not None:
        optional["feedback"] = FeedbackOut(rating=analysis.feedback.rating, comment=analysis.feedback.comment)
    present, missing = _skills(analysis, catalog)
    return AnalysisOut(
        analysis_id=analysis.id,
        status=analysis.status,
        target_role=_role(analysis),
        present_skills=present,
        missing_skills=missing,
        error=_error(analysis),
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        **optional,
    )


def _summary(analysis: Analysis) -> AnalysisSummaryOut:
    optional: dict[str, Any] = {}
    if analysis.match_score is not None:
        optional["match_score"] = float(analysis.match_score)
    return AnalysisSummaryOut(
        analysis_id=analysis.id,
        status=analysis.status,
        target_role=_role(analysis),
        error=_error(analysis),
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        **optional,
    )


@router.get(
    "",
    response_model=AnalysisListOut,
    response_model_exclude_unset=True,
    summary="Geçmiş analizlerim",
    responses={401: {"description": "Giriş gerekli", **_PROBLEM}},
)
def list_analyses(
    user: CurrentUser,
    service: Analyses,
    settings: AppSettings,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalysisListOut:
    """Yeniden eskiye. Sadece kullanıcının kendi, silinmemiş analizleri."""
    response.headers["Cache-Control"] = "no-store"
    rows, total = service.history(user.id, limit, offset, timedelta(seconds=settings.analysis_stale_after_s))
    return AnalysisListOut(items=[_summary(a) for a in rows], total=total)


@router.post(
    "",
    status_code=202,
    response_model=AnalysisCreated,
    summary="CV yükle ve analiz başlat",
    dependencies=[AnalysesRateLimit],
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        403: {"description": "Açık rıza geri alınmış", **_PROBLEM},
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
    except ConsentWithdrawn:
        return problem(
            403,
            "CV analizi için açık rızan geri alınmış. Profil → Verilerim bölümünden yeniden verebilirsin.",
            request,
            code="CONSENT_WITHDRAWN",
        )
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
    response_model_exclude_unset=True,
    summary="Analiz durumu ve sonucu",
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        404: {"description": "Analiz bulunamadı", **_PROBLEM},
    },
)
def get_analysis(
    analysis_id: uuid.UUID, user: CurrentUser, service: Analyses, settings: AppSettings, response: Response
) -> AnalysisOut:
    """Durum: queued, processing, done, failed. Başkasının veya silinmiş analiz 404 döner."""
    response.headers["Cache-Control"] = "no-store"
    analysis = service.get(analysis_id, user.id, timedelta(seconds=settings.analysis_stale_after_s))
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    return _out(analysis, service.catalog_for(analysis))


@router.post(
    "/{analysis_id}/feedback",
    response_model=FeedbackOut,
    summary="Analize geri bildirim (1-5 yıldız + yorum)",
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        404: {"description": "Analiz bulunamadı", **_PROBLEM},
        409: {"description": "Analiz henüz tamamlanmadı", **_PROBLEM},
        422: {"description": "Puan 1-5 dışında veya yorum 1000 karakterden uzun", **_PROBLEM},
    },
)
def give_feedback(
    request: Request, analysis_id: uuid.UUID, body: FeedbackIn, user: CurrentUser, service: Analyses
) -> FeedbackOut | JSONResponse:
    """Analiz başına tek geri bildirim; tekrar gönderilirse öncekinin yerine geçer."""
    try:
        found = service.give_feedback(analysis_id, user.id, body.rating, body.comment)
    except AnalysisNotFinished:
        return problem(409, "Geri bildirim analiz tamamlanınca verilebilir.", request)
    if not found:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    return FeedbackOut(rating=body.rating, comment=body.comment)


@router.delete(
    "/{analysis_id}",
    status_code=204,
    summary="Analizi sil",
    responses={
        401: {"description": "Giriş gerekli", **_PROBLEM},
        404: {"description": "Analiz bulunamadı", **_PROBLEM},
    },
)
def delete_analysis(analysis_id: uuid.UUID, user: CurrentUser, service: Analyses) -> Response:
    """Analiz hemen listeden ve sonuçtan kalkar, 30 gün içinde kalıcı silinir. Başkasının analizi de 404 döner."""
    if not service.delete(analysis_id, user.id):
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    return Response(status_code=204)
