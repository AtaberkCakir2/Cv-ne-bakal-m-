import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.db.enums import AnalysisErrorCode, AnalysisStatus

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


class AnalysisOut(BaseModel):
    """contracts/analysis_result.schema.json. Yetkinlik ve öneri listeleri T-048'de doldurulacak."""

    analysis_id: uuid.UUID
    status: AnalysisStatus
    target_role: TargetRoleOut
    postings_analyzed: int | None = None
    match_score: float | None = None
    present_skills: list[dict[str, Any]] = []
    missing_skills: list[dict[str, Any]] = []
    model: AnalysisModelOut | None = None
    error: AnalysisErrorOut | None = None
    created_at: datetime
    completed_at: datetime | None = None
