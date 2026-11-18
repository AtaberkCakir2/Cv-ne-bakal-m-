"""Profil ve KVKK uçlarının şemaları (T-049)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.enums import AnalysisStatus, ConsentType, UserRole
from app.schemas.auth import ConsentIn


class RoleRef(BaseModel):
    id: int
    slug: str  # contracts: role_slug
    name: str


class ProfileOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    is_verified: bool
    target_role: RoleRef | None


class ProfileUpdateIn(BaseModel):
    """Sadece gönderilen alanlar değişir; `null` göndermek alanı temizler. Bilinmeyen alan 422 verir."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"full_name": "Örnek Öğrenci", "target_role_id": 1}, {"target_role_id": None}]},
    )

    full_name: str | None = Field(default=None, max_length=120)
    target_role_id: int | None = Field(default=None, description="GET /roles listesindeki pozisyonun id'si")

    @field_validator("full_name")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value is not None else None


class ConsentOut(BaseModel):
    consent_type: ConsentType
    version: str
    accepted_at: datetime
    withdrawn_at: datetime | None


class ConsentsIn(BaseModel):
    """Metnin yeni sürümü onaylanınca gönderilir. Aynı sürüm daha önce onaylandıysa tekrar kaydedilmez."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"consents": [{"consent_type": "acik_riza", "version": "2027-01"}]}]}
    )

    consents: list[ConsentIn] = Field(min_length=1)

    @field_validator("consents")
    @classmethod
    def _no_duplicate_types(cls, value: list[ConsentIn]) -> list[ConsentIn]:
        types = [c.consent_type for c in value]
        if len(types) != len(set(types)):
            raise ValueError("Her onay türü bir kez gönderilmeli.")
        return value


class DeleteAccountIn(BaseModel):
    """Çalınmış bir oturumla hesap silinemesin diye şifre tekrar istenir."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"password": "ornek-sifre-123"}]})

    # Uzunluk kuralı yok: kural sonradan değişirse eski şifreli kullanıcı yine hesabını silebilsin.
    password: str = Field(min_length=1, max_length=128)


# --- verilerimi indir (KVKK md. 11). Alan adları veritabanıyla aynı; kullanıcıya ait olmayan iç alanlar yok.
class ExportSession(BaseModel):
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    user_agent: str | None


class ExportSkill(BaseModel):
    skill: str
    kind: str
    level: str
    confidence: Decimal | None
    demand_ratio: Decimal | None
    priority: int | None


class ExportRecommendation(BaseModel):
    skill: str
    title: str
    url: str
    rank: int
    reason_text: str | None


class ExportAnalysis(BaseModel):
    id: uuid.UUID
    created_at: datetime
    target_role: str
    status: AnalysisStatus
    cv_sha256: str
    cv_pages: int | None
    match_score: Decimal | None
    postings_analyzed: int | None
    completed_at: datetime | None
    deleted_at: datetime | None  # silindiyse: 30 gün sonra kalıcı silinir
    duration_ms: int | None
    error_code: str | None
    model_name: str | None
    prompt_version: str | None
    skills: list[ExportSkill]
    unverified_skills: list[dict[str, Any]]
    recommendations: list[ExportRecommendation]
    feedback: dict[str, Any] | None


class ExportActivity(BaseModel):
    action: str  # login, data.export, account.delete_failed…
    created_at: datetime


class ExportOut(BaseModel):
    exported_at: datetime
    profile: ProfileOut
    created_at: datetime
    consents: list[ConsentOut]
    sessions: list[ExportSession]
    analyses: list[ExportAnalysis]
    activity: list[ExportActivity]
    note: str = (
        "CV dosyanız ve CV metniniz saklanmadığı için bu dosyada yoktur. "
        "cv_sha256, dosyanın parmak izidir; içerik bundan geri elde edilemez."
    )
