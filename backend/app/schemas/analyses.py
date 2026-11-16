import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.enums import AnalysisErrorCode, AnalysisStatus, LangCode, ResourceLevel, ResourceProvider, SkillLevel

ERROR_MESSAGES = {
    AnalysisErrorCode.PDF_UNREADABLE: "PDF dosyası okunamadı.",
    AnalysisErrorCode.PDF_TOO_LARGE: "PDF dosyası çok büyük.",
    AnalysisErrorCode.NO_TEXT_FOUND: "PDF dosyasında metin bulunamadı.",
    AnalysisErrorCode.LLM_TIMEOUT: "Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.",
    AnalysisErrorCode.INTERNAL: "Analiz tamamlanamadı. Lütfen tekrar deneyin.",
}


# contracts/examples/analysis_result.example.json (OpenAPI örneği; sözleşme dosyası Docker imajında yok).
ANALYSIS_EXAMPLE: dict[str, Any] = {
    "analysis_id": "3f6c2a9e-8d1b-4c7a-9e2f-1a2b3c4d5e6f",
    "status": "done",
    "target_role": {"slug": "backend-developer", "name": "Backend Developer"},
    "postings_analyzed": 150,
    "match_score": 62.5,
    "present_skills": [
        {"skill": "Python", "level": "advanced", "confidence": 0.94, "verified": True},
        {"skill": "SQL", "level": "beginner", "confidence": 0.81, "verified": True},
        {"skill": "Git", "level": "intermediate", "confidence": 0.88, "verified": True},
    ],
    "missing_skills": [
        {
            "skill": "Docker",
            "demand_ratio": 0.75,
            "priority": 1,
            "resources": [
                {
                    "resource_id": 101,
                    "title": "Örnek: Docker'a Giriş (Türkçe)",
                    "url": "https://example.com/docker-giris",
                    "provider": "youtube",
                    "language": "tr",
                    "level": "beginner",
                    "duration_min": 90,
                    "is_free": True,
                    "reason": (
                        "İncelenen 150 Backend Developer ilanının %75'i Docker istiyor; CV'nde Docker bulunamadı."
                    ),
                }
            ],
        },
        {
            "skill": "PostgreSQL",
            "demand_ratio": 0.62,
            "priority": 2,
            "resources": [
                {
                    "resource_id": 205,
                    "title": "Örnek: PostgreSQL Temelleri",
                    "url": "https://example.com/postgresql-temelleri",
                    "provider": "docs",
                    "language": "en",
                    "level": "beginner",
                    "duration_min": 120,
                    "is_free": True,
                    "reason": "İlanların %62'si PostgreSQL istiyor; temel SQL bilgin bu konuya hızlı geçmeni sağlar.",
                }
            ],
        },
    ],
    "model": {"name": "llama3.1:8b", "prompt_version": "v1"},
    "error": None,
    "created_at": "2026-11-20T10:00:00Z",
    "completed_at": "2026-11-20T10:01:12Z",
}


class AnalysisCreated(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"analysis_id": "3f6c2a9e-8d1b-4c7a-9e2f-1a2b3c4d5e6f", "status": "queued"}]}
    )

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


class FeedbackIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"rating": 4, "comment": "Önerilen kaynaklar işime yaradı."}]}
    )

    rating: int = Field(ge=1, le=5, description="1-5 yıldız")
    comment: str | None = Field(default=None, max_length=1000, description="İsteğe bağlı yorum")

    @field_validator("comment")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class FeedbackOut(BaseModel):
    rating: int
    comment: str | None


class AnalysisOut(BaseModel):
    """contracts/analysis_result.schema.json. `feedback` API'nin eki (sözleşmede yok): verildiyse yanıtta yer alır."""

    # Örnek, contracts/examples/analysis_result.example.json ile aynıdır (tests/test_openapi.py denetler).
    model_config = ConfigDict(json_schema_extra={"examples": [ANALYSIS_EXAMPLE]})

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
    feedback: FeedbackOut | None = None


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
