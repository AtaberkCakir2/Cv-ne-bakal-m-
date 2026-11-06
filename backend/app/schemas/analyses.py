import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.db.enums import AnalysisErrorCode, AnalysisStatus, LangCode, ResourceLevel, ResourceProvider, SkillLevel

ERROR_MESSAGES = {
    AnalysisErrorCode.PDF_UNREADABLE: "PDF dosyası okunamadı.",
    AnalysisErrorCode.PDF_TOO_LARGE: "PDF dosyası çok büyük.",
    AnalysisErrorCode.NO_TEXT_FOUND: "PDF dosyasında metin bulunamadı.",
    AnalysisErrorCode.LLM_TIMEOUT: "Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.",
    AnalysisErrorCode.INTERNAL: "Analiz tamamlanamadı. Lütfen tekrar deneyin.",
}


class AnalysisCreated(BaseModel):
    analysis_id: uuid.UUID
    status: Literal["queued", "processing", "done", "failed"]


class TargetRoleOut(BaseModel):
    slug: str
    name: str


class AnalysisModelOut(BaseModel):
    name: str
    prompt_version: str


class AnalysisErrorOut(BaseModel):
    code: AnalysisErrorCode
    message: str


class PresentSkillOut(BaseModel):
    skill: str
    level: SkillLevel
    confidence: float
    verified: bool


class ResourceOut(BaseModel):
    """Sadece veri tabanındaki kaynaklar (karar #10). Değeri olmayan isteğe bağlı alanlar yanıtta yer almaz."""

    resource_id: int
    title: str
    url: str
    provider: ResourceProvider
    language: LangCode | None = None
    level: ResourceLevel
    duration_min: int | None = None
    is_free: bool
    reason: str | None = None


class MissingSkillOut(BaseModel):
    skill: str
    demand_ratio: float
    priority: int
    resources: list[ResourceOut]


class AnalysisOut(BaseModel):
    """contracts/analysis_result.schema.json."""

    analysis_id: uuid.UUID
    status: AnalysisStatus
    target_role: TargetRoleOut
    postings_analyzed: int | None = None
    match_score: float | None = None
    present_skills: list[PresentSkillOut] = []
    missing_skills: list[MissingSkillOut] = []
    model: AnalysisModelOut | None = None
    error: AnalysisErrorOut | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisSummaryOut(BaseModel):
    """Geçmiş listesindeki satır: yetkinlik listeleri yok, ayrıntı için GET /analyses/{id}."""

    analysis_id: uuid.UUID
    status: AnalysisStatus
    target_role: TargetRoleOut
    match_score: float | None = None
    error: AnalysisErrorOut | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisListOut(BaseModel):
    items: list[AnalysisSummaryOut]
    total: int
