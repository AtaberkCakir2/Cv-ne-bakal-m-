"""Veritabanı enum'ları. Değerler contracts/ ve erd.dbml ile birebir aynıdır; değiştirmek migration ister."""

from enum import StrEnum

from sqlalchemy import Enum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class ConsentType(StrEnum):
    KVKK_AYDINLATMA = "kvkk_aydinlatma"
    ACIK_RIZA = "acik_riza"
    KULLANIM_KOSULLARI = "kullanim_kosullari"


class TokenPurpose(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"  # noqa: S105 — enum değeri, şifre değil


class SkillCategory(StrEnum):
    DIL = "dil"
    FRAMEWORK = "framework"
    VERITABANI = "veritabani"
    BULUT = "bulut"
    DEVOPS = "devops"
    ARAC = "arac"
    METODOLOJI = "metodoloji"
    SOFT = "soft"


class SourceType(StrEnum):
    API = "api"
    SCRAPE = "scrape"
    DATASET = "dataset"


class LangCode(StrEnum):
    TR = "tr"
    EN = "en"


class SkillImportance(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class ScrapeStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ResourceProvider(StrEnum):
    YOUTUBE = "youtube"
    UDEMY = "udemy"
    COURSERA = "coursera"
    BTK_AKADEMI = "btk_akademi"
    DOCS = "docs"
    BLOG = "blog"
    OTHER = "other"


class ResourceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    UNKNOWN = "unknown"


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class AnalysisErrorCode(StrEnum):
    PDF_UNREADABLE = "PDF_UNREADABLE"
    PDF_TOO_LARGE = "PDF_TOO_LARGE"
    NO_TEXT_FOUND = "NO_TEXT_FOUND"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    INTERNAL = "INTERNAL"


class SkillKind(StrEnum):
    PRESENT = "present"
    MISSING = "missing"


def pg_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """PostgreSQL native enum; DB'ye Python adları değil değerler (ör. "acik_riza") yazılır."""
    return Enum(enum_cls, name=name, values_callable=lambda cls: [m.value for m in cls])
